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
    QVBoxLayout, QLabel, QComboBox
)

class RillaMainWindow(QMainWindow):
    """Main window for the Rilla application."""
    def __init__(self):
        super().__init__()
        # ... rest of the code is exactly the same as before ...

        # --- Basic Window Configuration ---
        self.setWindowTitle("Rilla - MOSFET Characterization Tool")
        self.setGeometry(100, 100, 400, 200) # x, y, width, height

        # --- Main Layout and Central Widget ---
        layout = QVBoxLayout()
        
        # --- UI Elements ---
        self.model_label = QLabel("Select MOSFET Model:")
        self.model_selector = QComboBox()

        layout.addWidget(self.model_label)
        layout.addWidget(self.model_selector)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # --- Load Data ---
        self.load_models()

    def load_models(self):
        """Reads the models.json file and populates the dropdown."""
        try:
            # Assuming you run from the root rilla-core directory
            with open("src/models.json", 'r') as f:
                data = json.load(f)
                model_names = [model['name'] for model in data['models']]
                self.model_selector.addItems(model_names)
        except FileNotFoundError:
            print("Error: models.json not found!")
            self.model_selector.addItem("Could not load models")
            self.model_selector.setEnabled(False)

# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RillaMainWindow()
    window.show()
    sys.exit(app.exec())