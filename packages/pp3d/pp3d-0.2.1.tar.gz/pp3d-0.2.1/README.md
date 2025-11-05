[简体中文](https://github.com/codeboyzhou/PathPlanner3D/blob/main/README_zh_CN.md) | [English](https://github.com/codeboyzhou/PathPlanner3D/blob/main/README.md)

<p align="center">
  <img src="https://img.shields.io/pypi/pyversions/pp3d?color=brightgreen" alt="Python Versions">
  <a href="https://pypi.org/project/pp3d/"><img src="https://img.shields.io/pypi/v/pp3d?color=brightgreen" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/pp3d/"><img src="https://img.shields.io/pepy/dt/pp3d?label=pypi%20%7C%20downloads&color=brightgreen" alt="Pepy Total Downloads"/></a>
</p>

## Overview

**PathPlanner3D** is an open-source, Python-based framework for 3D path planning, specifically designed for research and experimentation. Its core philosophy is "terrain awareness", integrating various metaheuristic optimization algorithms: Genetic Algorithm (GA), Particle Swarm Optimization (PSO), and a hybrid PSO-GA, with an interactive simulation and visualization environment.

This framework aims to provide a flexible and extensible experimental platform for researchers and developers in fields like UAV trajectory planning. With its highly modular architecture, users can easily validate new algorithms, compare the performance of different strategies, and conduct intuitive visual analysis in dynamically generated 3D terrains.

## Key Features

*   **Multiple Optimization Algorithms**: Includes built-in Genetic Algorithm (GA), Particle Swarm Optimization (PSO), and an innovative hybrid PSO-GA, all with dynamic parameter tuning.
*   **Terrain Awareness**: Ensures path feasibility in complex terrains through intelligent collision avoidance, featuring vertical height checks and horizontal obstacle detection (e.g. mountains).
*   **Interactive Playground**: Built with Streamlit, it supports real-time parameter adjustments, parallel comparison of multiple algorithms, and dynamic code editing with instant feedback.
*   **High-Quality 3D Visualization**: Uses Plotly to dynamically display 3D terrains, planned paths, and convergence curves, offering multi-angle views for analysis.
*   **Modular and Extensible Architecture**: A clean, layered design ("algorithm-common-visualization-playground") makes it easy to add new algorithms, customize fitness functions, or extend to new scenarios.
*   **Modern Engineering Practices**: Employs `pyproject.toml`, `uv` for dependency locking, and `pre-commit` for code quality assurance, ensuring project stability and maintainability.

## Tech Stack

The framework is built on a foundation of well-established libraries:
*   **Core**: NumPy, SciPy, Pydantic, Loguru
*   **Visualization**: Plotly
*   **Interactive UI**: Streamlit
*   **Development Tools**: `uv`, `pytest`, `ruff`, `pyright`, `pre-commit`

## Installation

**Prerequisites**: Python 3.12+

We recommend using `uv` for dependency management to ensure a consistent environment.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/codeboyzhou/PathPlanner3D.git
    cd PathPlanner3D
    ```

2.  **Install dependencies (Recommended)**:
    Use `uv` to sync dependencies.
    ```bash
    uv sync
    ```

3.  **Install dependencies (Alternative)**:
    If you prefer using `pip`, you can perform an editable installation.
    ```bash
    pip install -e .
    ```

## Quick Start

Activate the virtual environment:

```bash
.venv/Scripts/activate
```

Launch the Streamlit interactive playground with the following command:

```bash
streamlit run src/pp3d/playground/playground.py
```

After launching, a web interface will open automatically in your browser. You can:
1.  Select an algorithm (e.g. `PSO`) from the left sidebar.
2.  Adjust parameters like terrain, number of waypoints, and iterations.
3.  Click the `Run` button to see the generated 3D path and fitness convergence curve on the right.
4.  Try modifying the terrain generation logic or fitness function in the central code editor and observe the immediate impact on the results.

## Application Scenarios

*   **UAV Trajectory Planning**: Plan safe and efficient flight paths in complex environments like mountains or urban areas.
*   **Academic Research & Education**: Serve as a visual platform for teaching algorithms, comparing performance, and validating new theories.
