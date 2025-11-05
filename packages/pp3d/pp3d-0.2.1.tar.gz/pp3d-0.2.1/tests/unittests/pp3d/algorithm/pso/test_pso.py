import numpy as np

from pp3d.algorithm.pso.pso import PSOAlgorithm
from pp3d.algorithm.pso.types import PSOAlgorithmArguments


def fitness_function(x: np.ndarray) -> float:
    """Define a simple fitness function for testing."""
    return np.sum(x**2)


def test_run():
    """Test the complete run of the PSO algorithm."""
    algorithm_args = PSOAlgorithmArguments(
        num_particles=10,
        num_waypoints=5,
        max_iterations=10,
        inertia_weight=0.5,
        cognitive_weight=1.5,
        social_weight=1.5,
        max_velocities=(1.0, 1.0, 1.0),
        axes_min=(0.0, 0.0, 0.0),
        axes_max=(10.0, 10.0, 10.0),
        random_seed=42,
        verbose=False,
    )

    pso = PSOAlgorithm(algorithm_args, fitness_function)

    # Run the PSO algorithm
    best_path_points, best_fitness_values = pso.run()

    # Check the results
    assert best_path_points.shape == (algorithm_args.num_waypoints, 3)
    assert len(best_fitness_values) == algorithm_args.max_iterations

    # With a simple quadratic function, the best fitness should be non-negative and ideally close to zero
    assert best_fitness_values[-1] >= 0
