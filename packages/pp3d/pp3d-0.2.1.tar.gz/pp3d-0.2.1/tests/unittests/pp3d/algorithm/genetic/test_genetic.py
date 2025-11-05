import numpy as np

from pp3d.algorithm.genetic.genetic import GeneticAlgorithm
from pp3d.algorithm.genetic.types import GeneticAlgorithmArguments


def fitness_function(x: np.ndarray) -> float:
    """Define a simple fitness function for testing."""
    return np.sum(x**2)


def test_run():
    """Test the complete run of the genetic algorithm."""
    algorithm_args = GeneticAlgorithmArguments(
        population_size=10,
        tournament_size=3,
        num_waypoints=5,
        max_iterations=10,
        crossover_rate=0.8,
        mutation_rate=0.2,
        axes_min=(0.0, 0.0, 0.0),
        axes_max=(10.0, 10.0, 10.0),
        random_seed=42,
        verbose=False,
    )

    ga = GeneticAlgorithm(algorithm_args, fitness_function)

    best_path_points, best_fitness_values = ga.run()

    # Check return values
    assert isinstance(best_path_points, np.ndarray)
    assert isinstance(best_fitness_values, list)
    assert len(best_fitness_values) == algorithm_args.max_iterations

    # Check path points shape
    assert best_path_points.shape[1] == 3  # 3D coordinates
    assert best_path_points.shape[0] == algorithm_args.num_waypoints

    # With a simple quadratic function, the best fitness should be non-negative and ideally close to zero
    assert best_fitness_values[-1] >= 0
