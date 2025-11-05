import time
from collections.abc import Callable

import numpy as np
import streamlit as st
from loguru import logger

from pp3d.algorithm.pso.pso import PSOAlgorithm
from pp3d.algorithm.pso.types import PSOAlgorithmArguments
from pp3d.algorithm.types import AlgorithmArguments
from pp3d.playground import i18n
from pp3d.playground.types import AlgorithmRunningResult


def init_algorithm_args(common_algorithm_args: AlgorithmArguments) -> PSOAlgorithmArguments:
    """Initialize PSO algorithm arguments for the 3D Path Planning Playground.

    Args:
        common_algorithm_args (AlgorithmArguments): The common algorithm arguments.

    Returns:
        PSOAlgorithmArguments: The initialized PSO algorithm arguments for the 3D Path Planning Playground.
    """
    with st.expander(label=i18n.translate("pso_arguments"), expanded=True):
        num_particles = st.number_input(
            i18n.translate("number_of_particles"), min_value=10, max_value=100, value=50, step=10
        )
        inertia_weight = st.number_input(
            i18n.translate("inertia_weight"), min_value=0.1, max_value=1.0, value=0.5, step=0.1
        )
        cognitive_weight = st.number_input(
            i18n.translate("cognitive_weight"), min_value=0.1, max_value=2.1, value=1.5, step=0.1
        )
        social_weight = st.number_input(
            i18n.translate("social_weight"), min_value=0.1, max_value=2.1, value=1.5, step=0.1
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
        return PSOAlgorithmArguments(
            num_particles=num_particles,
            num_waypoints=common_algorithm_args.num_waypoints,
            max_iterations=common_algorithm_args.max_iterations,
            inertia_weight=inertia_weight,
            cognitive_weight=cognitive_weight,
            social_weight=social_weight,
            max_velocities=(max_velocity_x, max_velocity_y, max_velocity_z),
            axes_min=common_algorithm_args.axes_min,
            axes_max=common_algorithm_args.axes_max,
            random_seed=common_algorithm_args.random_seed,
            verbose=common_algorithm_args.verbose,
        )


def run_algorithm(
    args: PSOAlgorithmArguments, fitness_function: Callable[[np.ndarray], float], times: int = 1
) -> AlgorithmRunningResult:
    """Run the PSO algorithm for the 3D Path Planning Playground.

    Args:
        args (PSOAlgorithmArguments): The PSO algorithm arguments for the 3D Path Planning Playground.
        fitness_function (Callable[[np.ndarray], float]): The fitness function for the 3D Path Planning Playground.
        times (int, optional): The number of times to run the PSO algorithm. Defaults to 1.

    Returns:
        AlgorithmRunningResult: The running result of the PSO algorithm.
    """
    best_path_points = np.array([])
    best_fitness_values: list[float] = []
    best_fitness_value_samples: list[float] = []
    running_time_samples: list[float] = []

    for loop in range(times):
        logger.info(f"Running PSO algorithm, current progress {loop + 1}/{times}.")
        start_time = time.perf_counter()

        pso = PSOAlgorithm(args, fitness_function)
        best_path_points, best_fitness_values = pso.run()

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
