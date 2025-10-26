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

from PyLTSpice.raw.raw_read import RawRead
import numpy as np
from typing import Dict

def analyse(raw_file_path: str, analysis_params: Dict) -> Dict:
    """
    Standard analysis function for Vgs(th) characterization.

    Args:
        raw_file_path: The path to the LTSpice .raw simulation output file.
        analysis_params: A dictionary of parameters for the analysis,
                         including 'target_current'.

    Returns:
        A dictionary containing the structured analysis results.
    """

    target_current = analysis_params.get("target_current", 1e-3)

    ltr = RawRead(raw_file_path)

    def _find_drain_current_trace(ltr_instance):
        all_traces = ltr_instance.get_trace_names()
        possible_names = ["Ix(xu1:D)", "Ix(xu1:DRAIN)", "Id(XU1)", "Id(M1)"]
        for name in possible_names:
            for trace in all_traces:
                if trace.lower() == name.lower():
                    print(f"Found drain current trace: '{trace}'")
                    return ltr_instance.get_trace(trace)
        raise RuntimeError(f"Could not find a valid drain current trace. Available traces: {all_traces}")

    # Assuming temperature step is known from the template, not derived here.
    # For Vgs(th), we are typically interested in the 25°C case.
    # The new template definition includes temp steps, so this logic is simplified.
    # We find the step index corresponding to 25°C. A more robust implementation
    # would parse the .log file or have the engine pass this info.

    # Placeholder logic for finding the 25C step - assumes the standard range.
    # In a real scenario, this might need to be passed from the orchestration layer.
    try:
        temp_trace = ltr.get_trace('temp-sweep')
        temps = temp_trace.get_wave()
        step_idx = (np.abs(temps - 25)).argmin()
    except Exception:
        print("Warning: 'temp-sweep' trace not found. Defaulting to step 0.")
        step_idx = 0

    print(f"Analyzing simulation step {step_idx} (Temp ≈ 25°C)")

    vgs_trace = ltr.get_trace("V(v_g_d)")
    id_trace = _find_drain_current_trace(ltr)

    vgs_wave = vgs_trace.get_wave(step_idx).astype(float)
    id_wave = id_trace.get_wave(step_idx).astype(float)

    # Interpolate to find the threshold voltage at the target current
    vth = np.interp(target_current, id_wave, vgs_wave)

    return {
        "metrics": {
            "vth_at_25c_volts": float(vth),
            "target_current_amps": target_current
        },
        "curves": {
            "vth_curve": {
                "x_axis": {"name": "Vgs", "unit": "Volts", "data": vgs_wave.tolist()},
                "y_axis": {"name": "Id", "unit": "Amps", "data": id_wave.tolist()}
            }
        }
    }
