import time
from collections.abc import Callable

import numpy as np
import streamlit as st
from loguru import logger

from pp3d.algorithm.genetic.genetic import GeneticAlgorithm
from pp3d.algorithm.genetic.types import GeneticAlgorithmArguments
from pp3d.algorithm.types import AlgorithmArguments
from pp3d.playground import i18n
from pp3d.playground.types import AlgorithmRunningResult


def init_algorithm_args(common_algorithm_args: AlgorithmArguments) -> GeneticAlgorithmArguments:
    """Initialize genetic algorithm arguments for the 3D Path Planning Playground.

    Args:
        common_algorithm_args (AlgorithmArguments): The common algorithm arguments.

    Returns:
        GeneticAlgorithmArguments: The initialized genetic algorithm arguments for the 3D Path Planning Playground.
    """
    with st.expander(label=i18n.translate("genetic_arguments"), expanded=True):
        population_size = st.number_input(
            i18n.translate("population_size"), min_value=1, max_value=1000, value=100, step=1
        )
        tournament_size = st.number_input(i18n.translate("tournament_size"), min_value=2, max_value=10, value=3, step=1)
        crossover_rate = st.number_input(i18n.translate("crossover_rate"), min_value=0.0, max_value=1.0, value=0.8)
        mutation_rate = st.number_input(i18n.translate("mutation_rate"), min_value=0.0, max_value=1.0, value=0.2)
        return GeneticAlgorithmArguments(
            population_size=population_size,
            tournament_size=tournament_size,
            num_waypoints=common_algorithm_args.num_waypoints,
            max_iterations=common_algorithm_args.max_iterations,
            crossover_rate=crossover_rate,
            mutation_rate=mutation_rate,
            axes_min=common_algorithm_args.axes_min,
            axes_max=common_algorithm_args.axes_max,
            random_seed=common_algorithm_args.random_seed,
            verbose=common_algorithm_args.verbose,
        )


def run_algorithm(
    args: GeneticAlgorithmArguments, fitness_function: Callable[[np.ndarray], float], times: int = 1
) -> AlgorithmRunningResult:
    """Run the genetic algorithm for the 3D Path Planning Playground.

    Args:
        args (GeneticAlgorithmArguments): The genetic algorithm arguments for the 3D Path Planning Playground.
        fitness_function (Callable[[np.ndarray], float]): The fitness function for the 3D Path Planning Playground.
        times (int, optional): The number of times to run the genetic algorithm. Defaults to 1.

    Returns:
        AlgorithmRunningResult: The running result of the genetic algorithm.
    """
    best_path_points = np.array([])
    best_fitness_values: list[float] = []
    best_fitness_value_samples: list[float] = []
    running_time_samples: list[float] = []

    for loop in range(times):
        logger.info(f"Running GA algorithm, current progress {loop + 1}/{times}.")
        start_time = time.perf_counter()

        ga = GeneticAlgorithm(args, fitness_function)
        best_path_points, best_fitness_values = ga.run()

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
