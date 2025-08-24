# Copyright 2025 The Rilla Project Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QListWidget,
    QSplitter
)
from PySide6.QtCore import Qt, QThread, QObject, Signal

from simulation_engine import SimulationEngine
from analysis import VthExtractor


class Worker(QObject):
    """A worker that uses a pre-existing simulation engine."""
    finished = Signal()
    error = Signal(str)
    result = Signal(float)
    progress = Signal(str)

    # --- CHANGED: The worker now receives the engine instance ---
    def __init__(self, simulation_engine, model_info):
        super().__init__()
        self.engine = simulation_engine
        self.model_info = model_info

    def run_simulation_task(self):
        try:
            self.progress.emit(f"Running simulation for {self.model_info['name']}...")
            
            # --- CHANGED: No longer creates its own engine ---
            # 1. Run the simulation using the provided engine
            raw_file = self.engine.run_vth_simulation(
                model_name=self.model_info['name'],
                model_path=self.model_info['path']
            )

            if raw_file is None:
                raise RuntimeError("Simulation failed. Check console for details.")

            self.progress.emit("Analyzing results...")
            
            # 2. Analyze the results (this part is unchanged)
            extractor = VthExtractor(raw_file_path=raw_file)
            vth_value = extractor.extract_vth_at_25c(target_current=1e-3)

            if vth_value is None:
                raise RuntimeError("Failed to extract Vth from simulation data.")

            self.result.emit(vth_value)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class RillaMainWindow(QMainWindow):
    """Main window for the Rilla application."""
    def __init__(self):
        super().__init__()
        self.config_data = self.load_config()
        if not self.config_data:
            sys.exit(1)
        
        # --- NEW: Create a single, persistent SimulationEngine instance ---
        self.engine = SimulationEngine()
        # --- END OF NEW CODE ---

        self.setWindowTitle("Rilla - MOSFET Characterization")
        self.setGeometry(100, 100, 800, 600)

        self._create_menu_bar()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        main_splitter = QSplitter(Qt.Horizontal)
        config_panel = self._create_config_panel()
        
        # Corrected initialization from the previous fix
        self.results_panel = QWidget()
        self.results_panel.setLayout(QVBoxLayout())
        self.show_initial_message()

        main_splitter.addWidget(config_panel)
        main_splitter.addWidget(self.results_panel)
        main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(main_splitter)
        
        self.thread = None
        self.worker = None

    # ... load_config, _create_menu_bar, _create_config_panel methods are unchanged ...
    def load_config(self):
        try:
            with open("src/models.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("CRITICAL ERROR: models.json not found!")
            return None
        except json.JSONDecodeError:
            print("CRITICAL ERROR: models.json is not a valid JSON file!")
            return None

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        add_model_action = file_menu.addAction("Add Model...")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("About Rilla")
        return menu_bar

    def _create_config_panel(self):
        config_widget = QWidget()
        layout = QVBoxLayout()
        comp_group = QGroupBox("1. Select Component")
        comp_layout = QVBoxLayout()
        self.model_selector = QComboBox()
        model_names = [model['name'] for model in self.config_data.get('models', [])]
        self.model_selector.addItems(model_names)
        add_model_button = QPushButton("+ Add New Model")
        comp_layout.addWidget(QLabel("MOSFET Model:"))
        comp_layout.addWidget(self.model_selector)
        comp_layout.addWidget(add_model_button)
        comp_group.setLayout(comp_layout)
        test_group = QGroupBox("2. Select Test")
        test_layout = QVBoxLayout()
        self.test_list = QListWidget()
        self.test_list.addItems(["Vgs Threshold"])
        self.test_list.setCurrentRow(0)
        test_layout.addWidget(self.test_list)
        test_group.setLayout(test_layout)
        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.on_run_simulation_clicked)
        layout.addWidget(comp_group)
        layout.addWidget(test_group)
        layout.addStretch(1)
        layout.addWidget(self.run_button)
        config_widget.setLayout(layout)
        return config_widget

    def on_run_simulation_clicked(self):
        selected_model_name = self.model_selector.currentText()
        selected_model_info = next(
            (m for m in self.config_data['models'] if m['name'] == selected_model_name), None
        )
        if not selected_model_info:
            self.status_bar.showMessage("Error: Could not find selected model info.")
            return

        self.run_button.setEnabled(False)
        self.clear_results_panel()
        
        self.thread = QThread()
        # --- CHANGED: Pass the persistent engine to the worker ---
        self.worker = Worker(
            simulation_engine=self.engine,
            model_info=selected_model_info
        )
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run_simulation_task)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.display_vth_result)
        self.worker.error.connect(self.display_error)
        self.worker.progress.connect(self.update_status)
        self.thread.finished.connect(lambda: self.run_button.setEnabled(True))
        
        self.thread.start()

    # ... all other methods (update_status, display_error, etc.) are unchanged ...
    def update_status(self, message):
        self.status_bar.showMessage(message)

    def display_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}")
        error_label = QLabel(f"Simulation Failed\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: red;")
        self.results_panel.layout().addWidget(error_label)
        
    def display_vth_result(self, vth_value):
        self.status_bar.showMessage("Simulation complete.")
        result_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Vgs Threshold Result")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        model_label = QLabel(f"Component: {self.model_selector.currentText()}")
        result_label = QLabel(f"Vgs(th) @ 1mA, 25°C:")
        result_value = QLabel(f"{vth_value:.4f} V")
        result_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #007BFF;")
        layout.addWidget(title)
        layout.addWidget(model_label)
        layout.addSpacing(20)
        layout.addWidget(result_label)
        layout.addWidget(result_value)
        layout.addStretch()
        result_widget.setLayout(layout)
        self.results_panel.layout().addWidget(result_widget)

    def clear_results_panel(self):
        for i in reversed(range(self.results_panel.layout().count())): 
            self.results_panel.layout().itemAt(i).widget().setParent(None)

    def show_initial_message(self):
        self.clear_results_panel()
        initial_message = QLabel("Select a component and test, then press 'Run Simulation' to view results.")
        initial_message.setAlignment(Qt.AlignCenter)
        self.results_panel.layout().addWidget(initial_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RillaMainWindow()
    window.show()
    sys.exit(app.exec())