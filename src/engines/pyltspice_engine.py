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
from PySide6 import QtCore
from PyLTSpice import SimRunner, SpiceEditor

# Correct, absolute imports from the 'src' root
from core.interfaces import AbstractSimulationEngine
from engines.analysis import VthExtractor

class PyLTSpiceEngine(AbstractSimulationEngine):
    def run_vth_simulation(self, model_info: Dict) -> str:
        runner = SimRunner()
        print(f"Starting Vth simulation for {model_info['name']}...")

        # --- SANDBOX ISOLATION FIX ---
        source_asc_path = Path("src/test_circuits/vth_test.asc").resolve()
        source_asy_path = Path("src/test_circuits/generic_nmos.asy").resolve()

        run_timestamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss_zzz")
        sandbox_dir = Path(os.getcwd()) / f"temp_sim_{model_info['name']}_{run_timestamp}"
        sandbox_dir.mkdir(exist_ok=True)
        
        isolated_asc_path = sandbox_dir / source_asc_path.name
        shutil.copy(source_asc_path, isolated_asc_path)
        shutil.copy(source_asy_path, sandbox_dir)
        # --- END OF FIX ---
        
        runner.output_folder = sandbox_dir
        try:
            netlist_path = runner.create_netlist(isolated_asc_path)
            if not netlist_path:
                raise RuntimeError("Failed to create .net file from isolated .asc.")

            netlist = SpiceEditor(netlist_path)
            netlist.set_element_model('XXU1', model_info['name'])
            netlist.add_instructions(
                f".lib \"{model_info['path']}\"",
                ".dc V1 0 5 0.05",
                ".step temp -55 175 10",
                ".options plotwinsize=0"
            )
            
            raw_file, log_file = runner.run_now(netlist)
            
            if not raw_file:
                log_content = ""
                if log_file and os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                raise RuntimeError(f"Simulation failed. Log: {log_content}")

            extractor = VthExtractor(raw_file_path=raw_file)
            result_dict = extractor.extract_vth_at_25c(target_current=1e-3)
            
            output_data = { "status": "success", "test_type": "vth_analysis", "model_name": model_info['name'], "results": result_dict['results'], "raw_data_vth_curve": result_dict['raw_data'] }
            return json.dumps(output_data, indent=4)
        except Exception as e:
            error_data = { "status": "error", "model_name": model_info['name'], "error_message": str(e) }
            return json.dumps(error_data, indent=4)
        finally:
            try:
                shutil.rmtree(sandbox_dir)
            except OSError as e:
                print(f"Error removing temporary directory {sandbox_dir}: {e}")