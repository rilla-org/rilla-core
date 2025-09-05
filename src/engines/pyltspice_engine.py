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

import os
import shutil
import json
from pathlib import Path
from typing import Dict

from PyLTSpice import SimRunner, SpiceEditor

# Import the interface we are implementing
from core.interfaces import AbstractSimulationEngine
# Import the analysis module, which now lives alongside the engine
from .analysis import VthExtractor

class PyLTSpiceEngine(AbstractSimulationEngine):
    """
    A concrete implementation of the simulation engine using PyLTSpice.
    """

    def __init__(self):
        """Initializes the PyLTSpice engine."""
        # This runner can be reused for all simulations handled by this engine instance.
        self.runner = SimRunner()

    def run_vth_simulation(self, model_info: Dict) -> str:
        """
        Runs the Vgs(th) simulation and returns the results as a JSON string.
        """
        print(f"Starting Vth simulation for {model_info['name']}...")

        asc_file_path = "src/test_circuits/vth_test.asc"
        output_dir = Path(os.getcwd()) / "temp_sim"
        output_dir.mkdir(exist_ok=True)
        
        self.runner.output_folder = output_dir

        netlist_path = None
        log_file = None

        try:
            netlist_path = self.runner.create_netlist(asc_file_path)
            if not netlist_path:
                raise RuntimeError("Failed to create .net file from .asc.")

            netlist = SpiceEditor(netlist_path)
            
            netlist.set_element_model('XXU1', model_info['name'])
            netlist.add_instructions(
                f".lib \"{model_info['path']}\"",
                ".dc V1 0 5 0.05",
                ".step temp -55 175 10",
                ".options plotwinsize=0"
            )
            
            raw_file, log_file = self.runner.run_now(netlist)
            
            if not raw_file:
                # In case of failure, read the log for a more detailed error
                raise RuntimeError("Simulation failed to produce a .raw file.")

            # If simulation is successful, run the analysis
            extractor = VthExtractor(raw_file_path=raw_file)
            result_dict = extractor.extract_vth_at_25c(target_current=1e-3)

            # Create the final JSON output
            output_data = {
                "status": "success",
                "test_type": "vth_analysis",
                "model_name": model_info['name'],
                "results": result_dict['results'],
                "raw_data_vth_curve": result_dict['raw_data']
            }
            return json.dumps(output_data, indent=4)

        except Exception as e:
            # If anything fails during the process, catch the exception
            # and return a standardized error JSON. The full traceback
            # will still be printed to the console by the main worker thread.
            print(f"An error occurred in the simulation engine: {e}") # A simple log
            error_data = {
                "status": "error",
                "model_name": model_info['name'],
                "error_message": str(e)
            }
            return json.dumps(error_data, indent=4)