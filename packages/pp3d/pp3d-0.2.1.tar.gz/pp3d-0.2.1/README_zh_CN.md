[简体中文](https://github.com/codeboyzhou/PathPlanner3D/blob/main/README_zh_CN.md) | [English](https://github.com/codeboyzhou/PathPlanner3D/blob/main/README.md)

<p align="center">
  <img src="https://img.shields.io/pypi/pyversions/pp3d?color=brightgreen" alt="Python Versions">
  <a href="https://pypi.org/project/pp3d/"><img src="https://img.shields.io/pypi/v/pp3d?color=brightgreen" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/pp3d/"><img src="https://img.shields.io/pepy/dt/pp3d?label=pypi%20%7C%20downloads&color=brightgreen" alt="Pepy Total Downloads"/></a>
</p>

## 项目概览

**PathPlanner3D** 是一个专为研究和实验设计的、基于Python的开源三维路径规划框架。它以“地形感知”为核心，集成了多种元启发式优化算法：遗传算法（GA）、粒子群优化算法（PSO）、PSO-GA混合算法），并提供了一个交互式的仿真与可视化环境。

本框架旨在为无人机飞行路径规划领域的研究人员和开发者提供一个灵活、可扩展的实验平台。通过高度模块化的架构，用户可以轻松验证新算法、对比不同策略的性能，并在动态生成的三维地形中进行直观的可视化分析。

## 核心功能

*   **多种优化算法**：内置遗传算法（GA）、粒子群优化算法（PSO）以及创新的PSO-GA混合算法，并支持动态参数调整。
*   **地形感知能力**：通过垂直高度检测和水平障碍物检测（如山峰）实现智能碰撞规避，确保路径在复杂地形中的可行性。
*   **交互式实验平台**：基于Streamlit构建，支持实时参数调整、多算法并行对比、以及动态代码编辑，即时反馈规划结果。
*   **高质量3D可视化**：利用Plotly动态展示三维地形、规划路径及收敛曲线，提供多视角观察与分析。
*   **模块化与可扩展架构**：清晰的”算法-通用代码-可视化-实验“分层设计，便于添加新算法、自定义适应度函数或扩展新场景。
*   **现代化的工程实践**：采用 `pyproject.toml`、`uv` 依赖锁定和 `pre-commit` 代码质量保障工具，确保项目稳定与可维护。

## 技术架构

项目遵循“关注点分离”的设计原则，将核心功能解耦到四个主要模块中：

*   `algorithm/`: 存放所有路径规划算法的实现，如GA、PSO等。
*   `common/`: 提供通用基础设施，包括碰撞检测、路径插值、数学工具等。
*   `visualization/`: 负责所有可视化功能，如3D地形渲染和数据绘图。
*   `playground/`: 构建交互式实验环境，编排算法、数据和可视化组件。

这种结构使得框架的各个部分都可以独立开发和测试，同时也为未来的功能扩展打下了坚实的基础。

## 安装指南

**环境要求**: Python 3.12+

我们推荐使用 `uv` 来管理依赖，以确保环境的一致性。

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/codeboyzhou/PathPlanner3D.git
    cd PathPlanner3D
    ```

2.  **安装依赖（推荐方式）**:
    使用 `uv` 同步依赖。
    ```bash
    uv sync
    ```

3.  **安装依赖（备选方式）**:
    如果你倾向于使用 `pip`，可以进行可编辑模式安装。
    ```bash
    pip install -e .
    ```

## 快速开始

激活虚拟环境：

```bash
.venv/Scripts/activate
```

通过以下命令启动Streamlit交互式实验平台：

```bash
streamlit run src/pp3d/playground/playground.py
```

启动后，浏览器将自动打开一个Web页面。你可以：
1.  在左侧边栏选择一个算法（如 `PSO`）。
2.  调整地形、航点数量、迭代次数等参数。
3.  点击“Run”按钮，在右侧观察生成的3D路径和适应度收敛曲线。
4.  在代码编辑器中，尝试修改地形生成逻辑或适应度函数，可以立即看到结果变化。

## 应用场景

*   **无人机飞行路径规划**: 在山区、城市等复杂环境下，规划安全、高效的飞行轨迹。
*   **学术研究与教学**: 作为算法教学、性能对比和新理论验证的可视化平台。
