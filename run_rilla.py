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
import os
from PySide6.QtWidgets import QApplication

# --- THE REAL FIX: Add the 'src' directory to Python's path ---
# This ensures that all sub-modules can find each other, regardless of
# where the script is run from.
# os.path.dirname(__file__) gives the directory of the current script (the project root)
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
# --- END OF FIX ---

# Now that the path is set, these imports will work correctly.
from main import RillaMainWindow
from engines.pyltspice_engine import PyLTSpiceEngine

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Create the concrete engine instance
    pyltspice_engine = PyLTSpiceEngine()
    
    # 2. Inject the engine into the main window (Dependency Injection)
    window = RillaMainWindow(engine=pyltspice_engine)
    
    window.show()
    sys.exit(app.exec())