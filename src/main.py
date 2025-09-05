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
import os
import shutil
from typing import Dict
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QGroupBox, QLabel, QComboBox, 
    QPushButton, QListWidget, QSplitter, QFileDialog
)
from PySide6.QtCore import Qt, QThread, QObject, Signal

from core.interfaces import AbstractSimulationEngine
from engines.pyltspice_engine import PyLTSpiceEngine


class Worker(QObject):
    finished = Signal()
    result = Signal(str) 
    progress = Signal(str)

    def __init__(self, engine: AbstractSimulationEngine, model_info: Dict):
        super().__init__()
        self.engine = engine
        self.model_info = model_info

    def run_simulation_task(self):
        try:
            self.progress.emit(f"Running simulation for {self.model_info['name']}...")
            json_result = self.engine.run_vth_simulation(model_info=self.model_info)
            self.result.emit(json_result)
        except Exception:
            error_data = {
                "status": "error",
                "model_name": self.model_info.get('name', 'Unknown'),
                "error_message": traceback.format_exc()
            }
            self.result.emit(json.dumps(error_data, indent=4))
        finally:
            self.finished.emit()


class RillaMainWindow(QMainWindow):
    def __init__(self, engine: AbstractSimulationEngine):
        super().__init__()
        self.engine = engine
        # Define paths for user models and config
        self.user_models_dir = Path("user_models")
        self.config_path = Path("src/models.json")
        self.user_models_dir.mkdir(exist_ok=True) # Ensure the directory exists

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

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"CRITICAL ERROR loading {self.config_path}: {e}")
            return None

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        
        # --- NEW: Connect the "Add Model" menu action ---
        add_model_action = file_menu.addAction("Add Model...")
        add_model_action.triggered.connect(self.on_add_model_clicked)
        
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
        
        # --- REFACTORED: Use a dedicated refresh method ---
        self._refresh_model_dropdown()
        
        # The Add button in the UI is for future use, we are using the File menu for now
        add_model_button = QPushButton("+ Add New Model")
        add_model_button.setEnabled(False) # Disable for now to avoid confusion
        
        comp_layout.addWidget(QLabel("MOSFET Model:"))
        comp_layout.addWidget(self.model_selector)
        comp_layout.addWidget(add_model_button)
        comp_group.setLayout(comp_layout)
        
        # ... (rest of the panel is unchanged) ...
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

    # --- NEW: Method to handle adding a model file ---
    def _get_subckt_name_from_file(self, file_path: Path) -> str | None:
        """Reads a .lib or .mod file and extracts the first .SUBCKT name."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    # Look for lines that start with .SUBCKT, case-insensitive
                    if line.strip().lower().startswith('.subckt'):
                        # The name is the second part of the line
                        parts = line.strip().split()
                        if len(parts) > 1:
                            return parts[1] # Return the subcircuit name
            return None # No .SUBCKT found
        except Exception as e:
            print(f"Could not read or parse {file_path}: {e}")
            return None
        
    def on_add_model_clicked(self):
        """Opens a file dialog, copies the file, and intelligently extracts the model name."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select SPICE Model Files",
            "",
            "SPICE Models (*.lib *.mod);;All Files (*)"
        )

        if not file_paths:
            # User canceled the dialog
            return

        added_models = 0
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            dest_path = self.user_models_dir / file_path.name
            
            # 1. Copy the file to our user_models directory
            try:
                shutil.copy(file_path, dest_path)
                print(f"Copied model file to {dest_path}")
            except Exception as e:
                print(f"Error copying file {file_path.name}: {e}")
                # In a real app, show a message box to the user
                continue # Skip to the next file
            
            model_name = self._get_subckt_name_from_file(dest_path)
            
            # If we can't find a .SUBCKT name, fall back to the filename as a guess
            if not model_name:
                print(f"Warning: Could not find .SUBCKT in {dest_path}. Using filename as model name.")
                model_name = file_path.stem

            # 2. Add the new model to our models.json config
            absolute_path = os.path.abspath(dest_path)
        
            new_model_entry = {
            "name": model_name,
            "path": absolute_path # Use the absolute path here
            }
            
            # Avoid adding duplicates
            if not any(m['name'] == model_name for m in self.config_data['models']):
                self.config_data['models'].append(new_model_entry)
                added_models += 1

        if added_models > 0:
            # 3. Save the updated config back to the file
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(self.config_data, f, indent=4)
                
                # 4. Refresh the UI to show the new model
                self._refresh_model_dropdown()
                self.status_bar.showMessage(f"Successfully added {added_models} new model(s).")
            except Exception as e:
                print(f"Error saving updated config to {self.config_path}: {e}")

    # --- NEW: Centralized method for populating the dropdown ---
    def _refresh_model_dropdown(self):
        """Clears and repopulates the model selector dropdown from config data."""
        self.model_selector.clear()
        model_names = [model['name'] for model in self.config_data.get('models', [])]
        self.model_selector.addItems(model_names)

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