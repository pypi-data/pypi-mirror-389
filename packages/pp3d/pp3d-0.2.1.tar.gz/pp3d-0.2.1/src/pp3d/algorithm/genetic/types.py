import numpy as np
from pydantic import BaseModel, ConfigDict

from pp3d.algorithm.types import AlgorithmArguments


class GeneticAlgorithmArguments(AlgorithmArguments):
    """A class for genetic algorithm arguments."""

    population_size: int
    """The population size of the genetic algorithm."""

    tournament_size: int = 3
    """The tournament size of the genetic algorithm. Defaults to 3."""

    crossover_rate: float
    """The crossover rate of the genetic algorithm."""

    mutation_rate: float
    """The mutation rate of the genetic algorithm."""


class Individual(BaseModel):
    """A class for individual in genetic algorithm."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Configuration for the model."""

    gene: np.ndarray
    """The gene of the individual.
    
    A one-dimensional array, in the form of [x1, y1, z1, x2, y2, z2, ...], is used to represent the coordinates of all
    waypoints on the target path. The use of a one-dimensional array aims to reduce code complexity.
    """

    fitness_value: float
    """The fitness value of the individual."""
