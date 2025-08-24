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

from PyLTSpice import SimRunner, SpiceEditor
import os
import shutil # NEW: Import the shutil library for file operations
from pathlib import Path

class SimulationEngine:
    """Handles the modification and execution of LTSpice simulations."""

    def __init__(self):
        """Initializes the SimulationEngine."""
        self.runner = SimRunner()

    def run_vth_simulation(self, model_name, model_path):
        """
        Runs the Vgs(th) characterization simulation using the correct workflow.

        Args:
            model_name (str): The name of the MOSFET model.
            model_path (str): The absolute path to the .lib or .mod file.

        Returns:
            str: The path to the generated .raw file, or None if simulation failed.
        """
        print(f"Starting Vth simulation for {model_name}...")

        # 1. Define paths and set up the temporary directory
        asc_file_path = "src/test_circuits/vth_test.asc" # The schematic to use
        output_dir = Path(os.getcwd()) / "temp_sim"
        output_dir.mkdir(exist_ok=True) # A cleaner way to create the directory
        
        # Configure the runner to use this output directory
        self.runner.output_folder = output_dir

        # 2. Use the runner to CONVERT the .asc to a .net file. 
        # Because the .asy is in the same folder as the .asc, LTspice will find it.
        netlist_path = self.runner.create_netlist(asc_file_path)
        if not netlist_path:
             print("Error: Failed to create .net file from .asc.")
             return None

        # 3. Use SpiceEditor to modify the newly created .net file
        netlist = SpiceEditor(netlist_path)
        
        # 4. Set the model and add all simulation directives
        netlist.set_element_model('XXU1', model_name)
        netlist.add_instructions(
            f".lib \"{model_path}\"",
            ".dc V1 0 5 0.05",
            ".step temp -55 175 10",
            ".options plotwinsize=0"
        )
        
        # 5. Run the simulation using the modified netlist object
        raw_file, log_file = self.runner.run_now(netlist)
        
        if raw_file: # This is the correct way to check for success
            print(f"Simulation successful. Raw file at: {raw_file}")
            return raw_file
        else:
            print(f"Error: Simulation failed with return code {self.runner.return_code}")
            with open(log_file, 'r') as f:
                print("--- SPICE Log ---")
                print(f.read())
                print("-----------------")
            return None