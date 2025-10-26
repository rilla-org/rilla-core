# Rilla Project Philosophy

This document outlines the core principles that guide the development of Rilla. Understanding these principles is essential for contributing to the project in a meaningful way.

## 1. Separation of Concerns is Paramount

The Rilla architecture is built on a strict separation between the **simulation engine**, the **analysis modules**, and the **user interface**.

*   **Engine:** The engine's only job is to run a simulation based on a template and produce raw data. It should have no knowledge of the *meaning* of that data.
*   **Analysis:** An analysis module's only job is to take raw simulation data and extract meaningful metrics. It should not know how the data was generated.
*   **UI/CLI:** The user interface's job is to orchestrate the engine and analysis modules, and to present the results to the user.

This separation allows us to:
*   Add new simulation engines without changing the analysis logic.
*   Add new analysis modules without changing the simulation engine.
*   Build different user interfaces (e.g., a web UI) on top of the same core logic.

## 2. Templates are the Source of Truth

Every simulation in Rilla is defined by a `.template.json` file. This file is the single source of truth for:

*   Which testbench to use.
*   What simulation parameters to set.
*   Which analysis module to run.

This template-driven approach ensures that all simulations are **reproducible**, **version-controllable**, and **extensible**.

## 3. Data is Structured and Schematized

All data in Rilla, from project files to journal entries, is defined by a clear JSON schema. This ensures that:

*   Data is consistent and predictable.
*   LLMs can easily generate and consume data.
*   The system is auditable and easy to debug.

## 4. Prompt-Driven Development

Rilla is designed to be developed in collaboration with Large Language Models (LLMs). This means that:

*   Code should be clear, concise, and well-documented.
*   Interfaces should be simple and well-defined.
*   Schemas should be self-explanatory.

By following these principles, we can leverage the power of LLMs to accelerate development and build a more robust and flexible platform.
