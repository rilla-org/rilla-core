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

import argparse
import json
import importlib.util
from pathlib import Path

from rilla_core.engines.ltspice_adapter import LTSpiceAdapter

def main():
    parser = argparse.ArgumentParser(description="Run a Rilla simulation template.")
    parser.add_argument("template_file", help="Path to the .template.json file.")
    parser.add_argument("model_name", help="Name of the MOSFET model to use.")
    args = parser.parse_args()

    # In a real CLI, model_info would be looked up from a central registry
    # For this scaffold, we'll assume a local models.json for simplicity
    with open("rilla_core/models.json", 'r') as f:
        models = json.load(f)

    model_info = next((m for m in models if m['name'] == args.model_name), None)
    if not model_info:
        print(f"Error: Model '{args.model_name}' not found in models.json.")
        return

    engine = LTSpiceAdapter()
    raw_file_path = engine.run_template(args.template_file, model_info)

    # Dynamically load and run the analysis module
    with open(args.template_file, 'r') as f:
        template_def = json.load(f)

    analysis_module_name = template_def['analysis']['module']
    analysis_params = template_def['analysis']['parameters']

    # Construct the path to the analysis module relative to the template file
    template_path = Path(args.template_file).resolve()
    analysis_module_path = template_path.parent / analysis_module_name

    spec = importlib.util.spec_from_file_location(
        "analysis_module",
        analysis_module_path
    )
    analysis_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analysis_module)

    results = analysis_module.analyse(raw_file_path, analysis_params)

    print("\\n--- Analysis Results ---")
    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
