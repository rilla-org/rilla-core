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

class VthExtractor:
    # ... (__init__ is the same) ...
    def __init__(self, raw_file_path):
        self.raw_file_path = raw_file_path
        self.ltr = RawRead(self.raw_file_path)

    def _find_drain_current_trace(self):
        """
        Attempts to find the drain current trace using a list of common names.
        This handles variations in SPICE model pin naming (D vs DRAIN).
        """
        # Get all available traces from the raw file
        all_traces = self.ltr.get_trace_names()
        
        # A list of possible drain current names to try, in order of preference
        possible_names = [
            "Ix(xu1:D)",      # Common convention (lowercase)
            "Ix(xu1:DRAIN)",  # Explicit pin name convention
            "Id(XU1)",        # Another common convention
            "Id(M1)"          # If the MOSFET is a simple M device
        ]

        for name in possible_names:
            # Check if this name exists in the list of available traces (case-insensitive)
            for trace in all_traces:
                if trace.lower() == name.lower():
                    print(f"Found drain current trace: '{trace}'")
                    return self.ltr.get_trace(trace) # Return the trace object
        
        # If no match was found after checking all possibilities
        raise RuntimeError(f"Could not find a valid drain current trace. Available traces: {all_traces}")

    def extract_vth_at_25c(self, target_current=1e-3):
        """
        Finds Vgs(th) and returns the results and raw data in a dictionary.
        """
        # ... (setup logic is the same) ...
        temps = np.arange(-55, 175.1, 10)
        try:
            step_idx = (np.abs(temps - 25)).argmin()
        except (ValueError, IndexError):
            step_idx = 0
            
        print(f"Analyzing simulation step {step_idx} (Temp ≈ {temps[step_idx]}°C)")
        
        # This can now raise an exception that the engine will catch
        vgs_trace = self.ltr.get_trace("V(v_g_d)")
        id_trace = self._find_drain_current_trace()
        
        vgs_wave = vgs_trace.get_wave(step_idx).astype(float)
        id_wave = id_trace.get_wave(step_idx).astype(float)

        vth = np.interp(target_current, id_wave, vgs_wave)

        # Return a structured dictionary instead of just a float
        return {
            "results": {
                "vth_at_25c_volts": float(vth)
            },
            "raw_data": {
                "vgs_volts": vgs_wave.tolist(), # Convert numpy arrays to lists for JSON
                "id_amps": id_wave.tolist()
            }
        }