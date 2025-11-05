import numpy as np
from pydantic import BaseModel, ConfigDict


class AlgorithmRunningResult(BaseModel):
    """A class for algorithm running result."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Configuration for the model."""

    best_path_points: np.ndarray
    """Best path points for algorithm."""

    best_fitness_values: list[float]
    """Best fitness values for algorithm."""

    best_fitness_value_samples: list[float]
    """Best fitness value samples for algorithm."""

    running_time_samples: list[float]
    """Running time samples for algorithm."""


class MultiAlgorithmFusionResult(BaseModel):
    """A class for multi-algorithm fusion result."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Configuration for the model."""

    pso_full_path_points: np.ndarray
    """Full path points for PSO algorithm fusion result."""

    pso_best_fitness_values: list[float]
    """Best fitness values for PSO algorithm fusion result."""

    ga_full_path_points: np.ndarray
    """Full path points for GA algorithm fusion result."""

    ga_best_fitness_values: list[float]
    """Best fitness values for GA algorithm fusion result."""

    pso_ga_hybrid_full_path_points: np.ndarray
    """Full path points for PSO-GA hybrid algorithm fusion result."""

    pso_ga_hybrid_best_fitness_values: list[float]
    """Best fitness values for PSO-GA hybrid algorithm fusion result."""
