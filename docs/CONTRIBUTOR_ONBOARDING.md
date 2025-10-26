# Rilla Contributor Onboarding

Welcome to the Rilla project! This guide will help you get set up and make your first contribution.

## 1. Core Philosophy

Before you write any code, please read our `PHILOSOPHY.md` document. It explains the "why" behind our architecture and will help you make design decisions that align with the project's goals.

## 2. Setting Up Your Environment

1.  **Clone the repository:** `git clone https://github.com/your-repo/rilla.git`
2.  **Create a virtual environment:** `python -m venv venv`
3.  **Activate the virtual environment:**
    *   Windows: `.\\venv\\Scripts\\activate`
    *   macOS/Linux: `source venv/bin/activate`
4.  **Install dependencies:** `pip install -r requirements.txt` (Note: `requirements.txt` will be created in a future step).

## 3. How to Contribute

1.  **Create a new template:**
    *   Create a new directory under `rilla_core/templates/`.
    *   Add a `template.json` file defining the simulation.
    *   Add an `analysis_module.py` file with an `analyse` function.
    *   Add the testbench (`.asc`) and any necessary symbol (`.asy`) files.
2.  **Add a new CLI command:**
    *   Create a new Python file in `rilla_core/cli/`.
    *   Use the `argparse` library to define the command-line interface.
3.  **Improve the simulation engine:**
    *   Modify `rilla_core/engines/ltspice_adapter.py` to add new features or improve performance.

## 4. Submitting Your Changes

1.  **Fork the repository.**
2.  **Create a new branch for your feature.**
3.  **Make your changes and commit them with a clear message.**
4.  **Push your branch and open a pull request.**

Thank you for contributing to Rilla!
