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
import uuid
import datetime

def main():
    parser = argparse.ArgumentParser(description="Create a new Rilla design journal entry.")
    parser.add_argument("journal_file", help="Path to the .jrc journal file.")
    parser.add_argument("--title", required=True, help="Title of the journal entry.")
    parser.add_argument("--author", required=True, help="Author of the journal entry.")
    parser.add_argument("--rationale", required=True, help="Rationale for the design decision.")
    parser.add_argument("--sim-results", help="Path to a JSON file with simulation results to embed.")
    args = parser.parse_args()

    try:
        with open(args.journal_file, 'r') as f:
            journal = json.load(f)
    except FileNotFoundError:
        print(f"Creating new journal file at {args.journal_file}")
        journal = {
            "journal_id": str(uuid.uuid4()),
            "created_timestamp": datetime.datetime.now().isoformat(),
            "project_name": "New Rilla Project", # Placeholder
            "entries": []
        }

    sim_results_data = {}
    if args.sim_results:
        with open(args.sim_results, 'r') as f:
            sim_results_data = json.load(f)

    new_entry = {
        "entry_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().isoformat(),
        "author": args.author,
        "title": args.title,
        "rationale": args.rationale,
        "simulation_results": sim_results_data
    }

    journal["entries"].append(new_entry)

    with open(args.journal_file, 'w') as f:
        json.dump(journal, f, indent=4)

    print(f"Successfully added new entry to {args.journal_file}")

if __name__ == "__main__":
    main()
