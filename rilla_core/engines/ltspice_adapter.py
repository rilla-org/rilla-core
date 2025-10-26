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
import datetime
from PyLTSpice import SimRunner, SpiceEditor

# Correct, absolute imports from the 'rilla_core' root
from rilla_core.core.interfaces import AbstractSimulationEngine

class LTSpiceAdapter(AbstractSimulationEngine):
    def run_template(self, template_path: str, model_info: Dict) -> str:
        """
        Runs a simulation based on a generic template definition.

        Args:
            template_path: The absolute path to the .template.json file.
            model_info: A dictionary containing model information ('name', 'path').

        Returns:
            The path to the generated raw simulation output file.
        """

        # 1. Load and validate the template definition
        template_path = Path(template_path).resolve()
        template_dir = template_path.parent
        with open(template_path, 'r') as f:
            template_def = json.load(f)

        sim_def = template_def.get("simulation", {})
        testbench_file = sim_def.get("testbench")
        if not testbench_file:
            raise ValueError("Template definition must contain a 'testbench' file.")

        runner = SimRunner()
        print(f"Starting simulation for template '{template_def.get('template_name')}' with model '{model_info['name']}'...")

        # 2. Create an isolated sandbox directory for the simulation run
        run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        sandbox_dir = Path(os.getcwd()) / f"temp_sim_{model_info['name']}_{run_timestamp}"
        sandbox_dir.mkdir(exist_ok=True)

        runner.output_folder = str(sandbox_dir)

        try:
            # 3. Copy all necessary files (testbench, symbols) to the sandbox
            source_asc_path = (template_dir / testbench_file).resolve()
            isolated_asc_path = sandbox_dir / source_asc_path.name
            shutil.copy(source_asc_path, isolated_asc_path)

            source_asy_path = (template_dir / "generic_nmos.asy").resolve()
            if source_asy_path.exists():
                shutil.copy(source_asy_path, sandbox_dir)
            else:
                print(f"Warning: Symbol file 'generic_nmos.asy' not found in {template_dir}. Simulation may fail if it's a dependency.")

            # 4. Create the netlist from the isolated schematic
            netlist_path = runner.create_netlist(str(isolated_asc_path))
            if not netlist_path:
                raise RuntimeError("Failed to create .net file from isolated .asc.")

            # 5. Inject model and simulation commands into the netlist
            netlist = SpiceEditor(netlist_path)
            netlist.set_element_model('XXU1', model_info['name'])

            sim_params = sim_def.get("parameters", {})
            sim_commands = sim_def.get("commands", [])

            injected_commands = [cmd.format(**sim_params) for cmd in sim_commands]

            lib_command = f".lib \"{model_info['path']}\""

            netlist.add_instructions(lib_command, *injected_commands)

            # 6. Run the simulation
            raw_file, log_file = runner.run_now(netlist, run_filename=f"sim_run.net")

            if not raw_file:
                log_content = ""
                if log_file and os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                raise RuntimeError(f"Simulation failed. See log for details: {log_content}")

            # 7. Success: Return the path to the raw file for analysis
            print(f"Simulation successful. Raw data at: {raw_file}")

            return raw_file

        except Exception as e:
            try:
                shutil.rmtree(sandbox_dir)
            except OSError as cleanup_e:
                print(f"Error removing temporary directory {sandbox_dir} during error handling: {cleanup_e}")
            raise e
