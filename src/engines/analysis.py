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
        id_trace = self.ltr.get_trace("Ix(xu1:D)")
        
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