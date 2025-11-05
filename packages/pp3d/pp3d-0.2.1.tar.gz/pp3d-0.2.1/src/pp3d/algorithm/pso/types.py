import numpy as np
from pydantic import BaseModel, ConfigDict

from pp3d.algorithm.types import AlgorithmArguments


class PSOAlgorithmArguments(AlgorithmArguments):
    """A class for PSO algorithm arguments."""

    num_particles: int
    """The number of particles in the swarm."""

    inertia_weight: float
    """The inertia weight."""

    cognitive_weight: float
    """The cognitive weight."""

    social_weight: float
    """The social weight."""

    max_velocities: tuple[float, float, float]
    """The maximum velocities of particle, corresponding to the axis x, y and z."""


class Particle(BaseModel):
    """A class for a particle in the swarm."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Configuration for the model."""

    position: np.ndarray
    """The position of the particle.
    
    A one-dimensional array, in the form of [x1, y1, z1, x2, y2, z2, ...], is used to represent the coordinates of all
    waypoints on the target path. The use of a one-dimensional array aims to reduce code complexity and better adapt to
    the PSO position update formula.
    """

    velocity: np.ndarray
    """The velocity of the particle.
    
    A one-dimensional array, in the form of [vx1, vy1, vz1, vx2, vy2, vz2, ...], is used to represent the velocities
    of all waypoints on the target path. The use of a one-dimensional array aims to reduce code complexity and better
    adapt to the PSO velocity update formula.
    """

    best_position: np.ndarray
    """The best position of the particle. It has the same shape as `position`."""

    best_fitness_value: float
    """The best fitness value of the particle."""
