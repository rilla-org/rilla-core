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
import traceback
from typing import Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QGroupBox, QLabel, QComboBox, 
    QPushButton, QListWidget, QSplitter
)
from PySide6.QtCore import Qt, QThread, QObject, Signal

# --- ARCHITECTURAL CHANGE: Import the abstraction, not the concrete implementation ---
from core.interfaces import AbstractSimulationEngine
# --- ARCHITECTURAL CHANGE: Import the concrete engine at the entry point ---
from engines.pyltspice_engine import PyLTSpiceEngine


class Worker(QObject):
    """
    Worker that runs a simulation task using the provided engine.
    It now receives and emits JSON strings, enforcing separation.
    """
    finished = Signal()
    # --- ARCHITECTURAL CHANGE: The result is now a JSON string ---
    result = Signal(str) 
    progress = Signal(str)

    def __init__(self, engine: AbstractSimulationEngine, model_info: Dict):
        super().__init__()
        self.engine = engine
        self.model_info = model_info

    def run_simulation_task(self):
        """The main task to be run in the worker thread."""
        try:
            self.progress.emit(f"Running simulation for {self.model_info['name']}...")
            
            # The worker now only knows about the abstract interface method
            json_result = self.engine.run_vth_simulation(model_info=self.model_info)

            self.result.emit(json_result)
        except Exception:
            # Create a standardized error JSON if the engine itself crashes
            error_data = {
                "status": "error",
                "model_name": self.model_info.get('name', 'Unknown'),
                "error_message": traceback.format_exc()
            }
            self.result.emit(json.dumps(error_data, indent=4))
        finally:
            self.finished.emit()


class RillaMainWindow(QMainWindow):
    """
    The main UI window. It is now decoupled from any specific engine.
    """
    # --- ARCHITECTURAL CHANGE: The window is initialized with an engine ---
    def __init__(self, engine: AbstractSimulationEngine):
        super().__init__()
        self.engine = engine # Store the engine instance
        self.config_data = self.load_config()
        if not self.config_data:
            sys.exit(1)

        self.setWindowTitle("Rilla - MOSFET Characterization")
        self.setGeometry(100, 100, 800, 600)

        self._create_menu_bar()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        main_splitter = QSplitter(Qt.Horizontal)
        config_panel = self._create_config_panel()
        
        self.results_panel = QWidget()
        self.results_panel.setLayout(QVBoxLayout())
        self.show_initial_message()

        main_splitter.addWidget(config_panel)
        main_splitter.addWidget(self.results_panel)
        main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(main_splitter)
        
        self.thread = None
        self.worker = None

    # ... (load_config, _create_menu_bar, _create_config_panel are mostly unchanged) ...
    def load_config(self):
        try:
            with open("src/models.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"CRITICAL ERROR loading models.json: {e}")
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
        # The worker now receives the abstract engine instance
        self.worker = Worker(
            engine=self.engine,
            model_info=selected_model_info
        )
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run_simulation_task)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # --- ARCHITECTURAL CHANGE: Connect to the new result handler ---
        self.worker.result.connect(self.handle_json_result)
        self.worker.progress.connect(self.update_status)
        self.thread.finished.connect(lambda: self.run_button.setEnabled(True))
        
        self.thread.start()

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def handle_json_result(self, json_string: str):
        """
        Parses the JSON result from the worker and routes it to the correct display method.
        """
        try:
            data = json.loads(json_string)
            if data.get("status") == "success":
                self.status_bar.showMessage("Simulation complete.")
                # We could have a router here for different test_types in the future
                self.display_vth_result(data)
            else:
                error_msg = data.get("error_message", "Unknown error")
                self.display_error(error_msg)
        except json.JSONDecodeError:
            self.display_error("Received invalid JSON from the simulation engine.")

    def display_error(self, error_message):
        self.status_bar.showMessage(f"Error: Simulation failed.")
        self.clear_results_panel()
        error_label = QLabel(f"Simulation Failed\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: red;")
        self.results_panel.layout().addWidget(error_label)
        
    def display_vth_result(self, data: Dict):
        """Displays the final Vth result from the parsed JSON data."""
        self.clear_results_panel()
        
        result_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        vth_value = data.get("results", {}).get("vth_at_25c_volts", float('nan'))

        title = QLabel("Vgs Threshold Result")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        model_label = QLabel(f"Component: {data.get('model_name', 'N/A')}")
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
            widget = self.results_panel.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def show_initial_message(self):
        self.clear_results_panel()
        initial_message = QLabel("Select a component and test, then press 'Run Simulation' to view results.")
        initial_message.setAlignment(Qt.AlignCenter)
        self.results_panel.layout().addWidget(initial_message)


# --- ARCHITECTURAL CHANGE: This file is now a module, not the main entry point ---
if __name__ == "__main__":
    # This block is now only for testing this file in isolation.
    # The main application entry point is run_rilla.py in the root directory.
    print("This file is not meant to be run directly.")
    print("Please run 'python run_rilla.py' from the project root.")