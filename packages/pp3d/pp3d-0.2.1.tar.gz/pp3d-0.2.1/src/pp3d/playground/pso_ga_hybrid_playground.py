import time
from collections.abc import Callable

import numpy as np
import streamlit as st
from loguru import logger

from pp3d.algorithm.hybrid.pso_ga_hybrid import HybridPSOAlgorithm
from pp3d.algorithm.hybrid.pso_types import HybridPSOAlgorithmArguments
from pp3d.algorithm.types import AlgorithmArguments
from pp3d.playground import i18n
from pp3d.playground.types import AlgorithmRunningResult


def init_algorithm_args(common_algorithm_args: AlgorithmArguments) -> HybridPSOAlgorithmArguments:
    """Initialize Hybrid PSO algorithm arguments for the 3D Path Planning Playground.

    Args:
        common_algorithm_args (AlgorithmArguments): The common algorithm arguments.

    Returns:
        HybridPSOAlgorithmArguments: The Hybrid PSO algorithm arguments for the 3D Path Planning Playground.
    """
    with st.expander(label=i18n.translate("pso_ga_hybrid_arguments"), expanded=True):
        num_particles = st.number_input(
            i18n.translate("number_of_particles"), min_value=10, max_value=100, value=50, step=10
        )
        inertia_weight_min = st.number_input(
            i18n.translate("min_inertia_weight"), min_value=0.1, max_value=2.0, value=0.4, step=0.1
        )
        inertia_weight_max = st.number_input(
            i18n.translate("max_inertia_weight"), min_value=0.1, max_value=2.0, value=0.9, step=0.1
        )
        cognitive_weight_min = st.number_input(
            i18n.translate("min_cognitive_weight"), min_value=0.1, max_value=2.5, value=0.5, step=0.1
        )
        cognitive_weight_max = st.number_input(
            i18n.translate("max_cognitive_weight"), min_value=0.1, max_value=2.5, value=2.5, step=0.1
        )
        social_weight_min = st.number_input(
            i18n.translate("min_social_weight"), min_value=0.1, max_value=2.5, value=0.5, step=0.1
        )
        social_weight_max = st.number_input(
            i18n.translate("max_social_weight"), min_value=0.1, max_value=2.5, value=2.5, step=0.1
        )
        with st.expander(label=i18n.translate("max_velocities"), expanded=True):
            max_velocity_x = st.number_input(
                i18n.translate("max_velocity_x"), min_value=0.1, max_value=10.0, value=1.0, step=0.1
            )
            max_velocity_y = st.number_input(
                i18n.translate("max_velocity_y"), min_value=0.1, max_value=10.0, value=1.0, step=0.1
            )
            max_velocity_z = st.number_input(
                i18n.translate("max_velocity_z"), min_value=0.1, max_value=10.0, value=1.0, step=0.1
            )
        return HybridPSOAlgorithmArguments(
            num_particles=num_particles,
            num_waypoints=common_algorithm_args.num_waypoints,
            max_iterations=common_algorithm_args.max_iterations,
            inertia_weight_min=inertia_weight_min,
            inertia_weight_max=inertia_weight_max,
            cognitive_weight_min=cognitive_weight_min,
            cognitive_weight_max=cognitive_weight_max,
            social_weight_min=social_weight_min,
            social_weight_max=social_weight_max,
            max_velocities=(max_velocity_x, max_velocity_y, max_velocity_z),
            axes_min=common_algorithm_args.axes_min,
            axes_max=common_algorithm_args.axes_max,
            random_seed=common_algorithm_args.random_seed,
            verbose=common_algorithm_args.verbose,
        )


def run_algorithm(
    args: HybridPSOAlgorithmArguments, fitness_function: Callable[[np.ndarray], float], times: int = 1
) -> AlgorithmRunningResult:
    """Run the Hybrid PSO algorithm for the 3D Path Planning Playground.

    Args:
        args (HybridPSOAlgorithmArguments): The Hybrid PSO algorithm arguments for the 3D Path Planning Playground.
        fitness_function (Callable[[np.ndarray], float]): The fitness function for the 3D Path Planning Playground.
        times (int, optional): The number of times to run the Hybrid PSO algorithm. Defaults to 1.

    Returns:
        AlgorithmRunningResult: The running result of the Hybrid PSO algorithm.
    """
    best_path_points = np.array([])
    best_fitness_values: list[float] = []
    best_fitness_value_samples: list[float] = []
    running_time_samples: list[float] = []

    for loop in range(times):
        logger.info(f"Running Hybrid PSO algorithm, current progress {loop + 1}/{times}.")
        start_time = time.perf_counter()

        hybrid_pso = HybridPSOAlgorithm(args, fitness_function)
        best_path_points, best_fitness_values = hybrid_pso.run()

        end_time = time.perf_counter()
        duration = end_time - start_time

        best_fitness_value_samples.append(best_fitness_values[-1])
        running_time_samples.append(duration)

    return AlgorithmRunningResult(
        best_path_points=best_path_points,
        best_fitness_values=best_fitness_values,
        best_fitness_value_samples=best_fitness_value_samples,
        running_time_samples=running_time_samples,
    )
