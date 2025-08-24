This document records key architectural decisions and the future roadmap for the Rilla application's structure.

## 1. Configuration and User Data Management

### Current State (MVP)

For the initial MVP, all configuration, including the path to the LTSpice executable and the list of MOSFET models, is stored in a single `models.json` file located within the `src/` directory.

- **File:** `src/models.json`
- **Rationale:** This approach is simple and sufficient for initial development and testing, as it allows the core simulation and analysis functionality to be built without the overhead of a complex configuration system.

# Rilla Architecture Decisions

This document records key architectural decisions and the future roadmap for the Rilla application's structure.
## 2. Simulation Artifacts and Dependencies

### 2.1. Standardized Test Benches

All LTSpice test benches (`.asc` files) used for simulation must be designed for headless, automated execution. They must adhere to a strict "contract" to ensure they can be reliably parsed and modified by the `SimulationEngine`. This contract includes:

- **Standardized Placeholders:** Using `MODEL_PLACEOLDER` for the DUT's value and `!.lib MODEL_PATH_PLACEHOLDER` for the model library path.
- **Consistent Naming:** The DUT instance must always be named `XU1` to ensure predictable output trace names (e.g., `Ix(XU1:D)`).

### 2.2. Custom Symbol Dependency

To ensure simulation reliability and repeatability, our test benches do not use LTspice's built-in, default symbols for the DUT. Instead, we use a custom, standardized symbol (`generic_nmos.asy`).

- **Rationale:** This prevents the simulator from making incorrect assumptions, automatically including unwanted libraries, or generating an inconsistent netlist. It guarantees that our simulation environment is self-contained.
- **Architectural Impact:** The `generic_nmos.asy` file is a **required runtime dependency** for any simulation.
- **Implementation:** The `SimulationEngine` is responsible for managing this dependency. Before executing a simulation, it programmatically copies the required `.asy` file(s) from the application's bundled resources (e.g., `src/symbols/`) into the temporary directory where the simulation will be run. This ensures that LTspice can always find the symbol, regardless of the application's installation location or the user's local LTspice library configuration.
### Future State (Post-MVP / Public Release)

For a distributable application, hardcoded paths are not viable. The application must separate its own program files from user-specific data. The target architecture is as follows:

1.  **User-Specific Data Directory:** On first launch, the application will create a dedicated data directory in the user's standard application data location (e.g., `%APPDATA%\Rilla` on Windows).

2.  **Configuration File (`config.json`):**
    - This file will be created in the user's data directory.
    - It will store persistent user settings, most importantly the path to the `LTspice.exe` executable.
    - On first launch, the app will attempt to auto-detect the executable's location. If it fails, it will prompt the user to locate it manually.

3.  **Model Library (`models.json`):**
    - The user's personal library of MOSFET models will also be stored in their data directory.
    - The `models.json` file currently in the `src/` directory will be treated as a default template, copied to the user's data directory on first launch.
    - The UI will provide functionality to add/remove models, which will modify this user-specific file, not the application's bundled files.

4.  **Temporary Files:** All simulation output (`.raw`, `.log` files) will be generated in a `temp_sim` subfolder within the user's data directory to avoid cluttering the project or system folders.

This architecture ensures that user data is persistent, portable, and is not overwritten when the Rilla application itself is updated.