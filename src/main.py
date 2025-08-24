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
from PySide6.QtCore import Qt

class RillaMainWindow(QMainWindow):
    """Main window for the Rilla application."""
    def __init__(self):
        super().__init__()

        # --- Basic Window Configuration ---
        self.setWindowTitle("Rilla - MOSFET Characterization")
        self.setGeometry(100, 100, 800, 600) # Start with a larger window

        # --- Menu Bar ---
        self._create_menu_bar()

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

        # --- Main Layout (using a QSplitter) ---
        main_splitter = QSplitter(Qt.Horizontal)
        
        config_panel = self._create_config_panel()
        results_panel = self._create_results_panel()

        main_splitter.addWidget(config_panel)
        main_splitter.addWidget(results_panel)
        main_splitter.setStretchFactor(1, 1) # Make the results panel larger

        self.setCentralWidget(main_splitter)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        add_model_action = file_menu.addAction("Add Model...")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("About Rilla")
        return menu_bar

    def _create_config_panel(self):
        """Creates the left-hand configuration panel widget."""
        config_widget = QWidget()
        layout = QVBoxLayout()
        
        # Component Selection Group
        comp_group = QGroupBox("1. Select Component")
        comp_layout = QVBoxLayout()
        self.model_selector = QComboBox()
        self.load_models() # Populate the dropdown
        add_model_button = QPushButton("+ Add New Model")
        comp_layout.addWidget(QLabel("MOSFET Model:"))
        comp_layout.addWidget(self.model_selector)
        comp_layout.addWidget(add_model_button)
        comp_group.setLayout(comp_layout)

        # Test Selection Group
        test_group = QGroupBox("2. Select Test")
        test_layout = QVBoxLayout()
        self.test_list = QListWidget()
        self.test_list.addItems(["Vgs Threshold", "Rds(on) vs. Vgs", "Rds(on) vs. Temp"])
        test_layout.addWidget(self.test_list)
        test_group.setLayout(test_layout)

        # Action Button
        run_button = QPushButton("Run Simulation")
        # In a future step, we will connect this: run_button.clicked.connect(...)

        layout.addWidget(comp_group)
        layout.addWidget(test_group)
        layout.addStretch(1) # Pushes the button to the bottom
        layout.addWidget(run_button)
        
        config_widget.setLayout(layout)
        return config_widget

    def _create_results_panel(self):
        """Creates the right-hand results panel widget."""
        results_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Initial message
        initial_message = QLabel("Select a component and test, then press 'Run Simulation' to view results.")
        initial_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(initial_message)

        # This layout will be cleared and populated with results later
        results_widget.setLayout(layout)
        return results_widget

    def load_models(self):
        """Reads the models.json file and populates the dropdown."""
        try:
            with open("src/models.json", 'r') as f:
                data = json.load(f)
                model_names = [model['name'] for model in data['models']]
                self.model_selector.addItems(model_names)
        except FileNotFoundError:
            self.statusBar().showMessage("Error: models.json not found!")
            self.model_selector.addItem("Could not load models")
            self.model_selector.setEnabled(False)

# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RillaMainWindow()
    window.show()
    sys.exit(app.exec())