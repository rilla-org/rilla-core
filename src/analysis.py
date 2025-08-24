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
    """Extracts Vgs(th) from a simulation raw file."""

    def __init__(self, raw_file_path):
        self.raw_file_path = raw_file_path
        self.ltr = RawRead(self.raw_file_path)

    def extract_vth_at_25c(self, target_current=1e-3):
        """
        Finds the Vgs threshold at or near 25°C for a given target current.
        ... (docstring is the same) ...
        """
        temps = np.arange(-55, 176, 10)
        
        try:
            step_idx = (np.abs(temps - 25)).argmin()
        except (ValueError, IndexError):
            step_idx = 0

        print(f"Analyzing simulation step {step_idx} (Temp ≈ {temps[step_idx]}°C)")

        try:
            vgs_trace = self.ltr.get_trace("V(v_g_d)")
            id_trace = self.ltr.get_trace("Ix(xu1:D)") 
            
            vgs_wave = vgs_trace.get_wave(step_idx)
            id_wave = id_trace.get_wave(step_idx)

            # Convert data waves to floating point numbers
            
            vgs_wave = vgs_wave.astype(float)
            id_wave = id_wave.astype(float)


            # Interpolate to find the Vgs that corresponds to the target current
            vth = np.interp(target_current, id_wave, vgs_wave)
            return float(vth)

        except Exception as e:
            print(f"Error during data extraction: {e}")
            return None