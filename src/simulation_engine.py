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

class SimulationEngine:
    """Handles the modification and execution of LTSpice simulations."""

    def __init__(self):
        """Initializes the SimulationEngine."""
        self.runner = SimRunner()

    def run_vth_simulation(self, model_name, model_path):
        """
        Runs the Vgs(th) characterization simulation.

        Args:
            model_name (str): The name of the MOSFET model (e.g., "PSMN1R4-100CSE").
            model_path (str): The absolute path to the .lib or .mod file.

        Returns:
            str: The path to the generated .raw file, or None if simulation failed.
        """
        print(f"Starting Vth simulation for {model_name}...")

        # 1. Create a SpiceEditor instance from our template file
        netlist = SpiceEditor("src/test_circuits/vth_test.asc")

        # 2. Replace the placeholders in the netlist
        netlist.set_element_model('XU1', model_name)
        # Use add_instructions to add the .lib command. We use a comment in the .asc as a placeholder.
        netlist.add_instructions(f".lib \"{model_path}\"") # Enclose path in quotes for safety

        # 3. Set up a temporary directory for the simulation output
        output_dir = os.path.join(os.getcwd(), "temp_sim")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # --- NEW: Handle the custom symbol dependency ---
        # Copy our standard symbol to the simulation directory so LTspice can find it.
        symbol_source_path = "src/symbols/generic_nmos.asy"
        symbol_dest_path = os.path.join(output_dir, "generic_nmos.asy")
        shutil.copy(symbol_source_path, symbol_dest_path)
        # --- END OF NEW CODE ---
        
        # Configure the runner to use this output directory
        self.runner.output_folder = output_dir

        raw_file, log_file = self.runner.run_now(netlist, run_filename="vth_run.net")
        
        if self.runner.return_code == 0:
            print(f"Simulation successful. Raw file at: {raw_file}")
            return raw_file
        else:
            print(f"Error: Simulation failed with return code {self.runner.return_code}")
            return None