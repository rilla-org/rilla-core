# Rilla Developer Notes

## 1. Introduction

This document is a living repository of technical knowledge, design patterns, and "gotchas" discovered during the development of Rilla. Its purpose is to onboard new developers quickly and to serve as a reference for the core team. It captures the non-obvious lessons learned that are critical for understanding and contributing to the project.

---

## 2. Project Configuration & Environment

### 2.1. Virtual Environment (venv)

The project uses a standard Python virtual environment (`venv`) to manage dependencies. **Activation is mandatory before running or testing the application.** All commands should be run from the project root directory.

#### On Windows (using PowerShell)

PowerShell's default security policy (`Restricted`) prevents the activation script from running. You must relax this policy for your current terminal session.

1.  **Open a new PowerShell terminal** in VSCode.
2.  **Set the Execution Policy for the current session.** This is a temporary change that is reset when the terminal is closed.
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    ```
3.  **Run the activation script.**
    ```powershell
    .\venv\Scripts\activate
    ```
4.  **Verification:** The terminal prompt will be prefixed with `(venv)`.

#### On macOS / Linux

1.  **Open a new terminal** (e.g., Bash, Zsh).
2.  **Run the activation script.**
    ```bash
    source venv/bin/activate
    ```
3.  **Verification:** The terminal prompt will be prefixed with `(venv)`.

### 2.2. Runtime Artifacts (`.gitignore`)

The repository is configured to ignore files that are generated at runtime. This keeps the source history clean and prevents unnecessary conflicts. Committing these files is strictly prohibited.

- **`/temp_sim/`**: This directory is created by the `SimulationEngine` to store all simulation outputs (`.raw`, `.log`, `.net`). It is ignored entirely.
- **`*.net`**: All SPICE netlist files are ignored. These are considered intermediate build artifacts, as they are generated from the source `.asc` schematic files.

---

## 3. PyLTSpice Library Integration Notes

The `PyLTSpice` library is the core of our simulation engine, but working with it requires a specific and non-obvious workflow. The following patterns **must** be followed to ensure reliable operation.

### 3.1. The Core Workflow: ASC -> NET -> Edit -> Run

The `SpiceEditor` class is designed to edit **netlist (`.net`) files**, not schematic (`.asc`) files. Attempting to parse an `.asc` file directly will lead to a cascade of errors. The only correct, reliable workflow is as follows:

1.  **Start with a clean schematic (`.asc`)** that contains only the circuit topology and placeholders. Do not include simulation directives like `.dc`, `.step`, or `.end` as text objects.
2.  Use a `SimRunner` instance to **convert the schematic to a netlist**. This is the most critical step. LTSpice's own engine is used for this conversion, which guarantees a valid, complete netlist is created (including the required `.end` statement).
    ```python
    runner = SimRunner()
    netlist_path = runner.create_netlist("path/to/schematic.asc")
    ```
3.  **Instantiate `SpiceEditor` on the newly created `.net` file.**
    ```python
    netlist = SpiceEditor(netlist_path)
    ```
4.  **Programmatically add all simulation directives** to the netlist object using `netlist.add_instructions()`. This is where `.lib`, `.dc`, `.step`, and `.options` commands are injected.
5.  **Run the simulation** using the modified netlist object: `runner.run_now(netlist)`.

### 3.2. Component & Trace Naming Discrepancies

The instance and trace names can change during the `ASC -> NET -> RAW` translation process. Relying on names from the schematic file will fail. The "ground truth" is always the generated files.

#### Instance Naming (`U1` -> `XXU1` -> `xu1`)
For our standardized `generic_nmos.asy` symbol with `InstName=U1`, the transformation is:
- **Schematic (`.asc`):** `U1`
- **Netlist (`.net`):** `XXU1`
- **Raw File (`.raw`):** `xu1` (lowercase)

**Conclusion:** Use `XXU1` in the `SpiceEditor` and `xu1` when parsing the `.raw` file.

#### Trace Pin Naming (`:D` vs `:DRAIN`)
The names of the pins in a current trace (e.g., `Ix(xu1:<pin_name>)`) are determined by the pin names defined in the model's `.SUBCKT` line.
- **Example 1:** `.SUBCKT MODEL_A D G S` will produce the trace `Ix(xu1:D)`.
- **Example 2:** `.SUBCKT MODEL_B DRAIN GATE SOURCE` will produce the trace `Ix(xu1:DRAIN)`.

**Conclusion:** The analysis module must be flexible. It cannot assume a single pin naming convention. Our `VthExtractor` implements a pattern that checks a list of common possibilities (`Ix(xu1:D)`, `Ix(xu1:DRAIN)`, etc.) to handle this variation.

### 3.3. Library Version Incompatibilities

During initial development, several incompatibilities were discovered with the version of `PyLTSpice` installed by `pip`. Future work will add a `requirements.txt` file to lock down versions, but developers should be aware of these known issues:

- **`SimRunner` Constructor:** The constructor does not accept `ltspice_exe` or `ltspice_exec` as a keyword argument. The library is expected to find the executable via the system's PATH. Instantiate with `SimRunner()`.
- **`output_folder` Type:** The `runner.output_folder` attribute **must** be a `pathlib.Path` object, not a string. Failure to do so causes a `TypeError` during path joining.
- **Success Check:** The `SimRunner` object does not have a `.return_code` attribute. A successful simulation is indicated when `runner.run_now()` returns a valid path string for the `raw_file`. A failed simulation returns `None`.

### 3.4. Data Type Handling in `.raw` Files

The data read from `.raw` files by `PyLTSpice` may not be in a numeric format. Before performing any mathematical operations (e.g., `numpy.interp`), the data arrays **must** be explicitly cast to a numeric type.

```python
# Always cast wave data to float before use
vgs_wave = vgs_trace.get_wave(step_idx).astype(float)
id_wave = id_trace.get_wave(step_idx).astype(float)
```

### 3.5. SPICE File & Symbol Dependencies
LTSpice has a strict dependency resolution path. For a simulation to run reliably from an .asc file:
Any custom symbols (e.g., generic_nmos.asy) must be located in the same directory as the .asc schematic that uses them.

### 3.6. Absolute vs. Relative Paths

The LTSpice simulation engine, when called from a script, does not know the context of the Python script's working directory. All paths passed into the generated netlist, especially for `.lib` files, **must be absolute paths**.

- **Implementation:** When a user adds a new model, the path stored in `models.json` must be converted to its full, absolute path (e.g., using `os.path.abspath()`). Passing a relative path like `user_models/model.lib` will result in a "Fatal Error: Could not open library file" from the simulator.

## 4. Future Architectural Plans

### 4.1. Logging Strategy
The current use of print() for debugging is temporary. The next major refactor will replace all print statements with Python's standard logging module.
Benefits: This will allow for configurable log levels (DEBUG, INFO, WARNING, ERROR), logging to a file (rilla.log), and providing users with a way to enable verbose logging for easier remote debugging.

### 4.2. Built-in Debugging Tools
To make future development easier, we plan to add a "Debug" menu to the application.
Export Last Netlist: A planned feature is a menu option that will save a copy of the exact .net file that was generated and sent to the simulator. This would have solved the "XXU1" naming issue instantly and will be invaluable for debugging future test benches.