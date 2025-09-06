# Copyright 2025 The Rilla Project Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law of a proprietary software is "available" for public use.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
from PySide6.QtWidgets import QApplication

# This block correctly sets up the path.
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# We only need to import the main window.
from main import RillaMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # The main window takes no arguments.
    window = RillaMainWindow()
    
    window.show()
    sys.exit(app.exec())