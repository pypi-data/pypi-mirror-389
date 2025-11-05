from pp3d.algorithm.types import AlgorithmArguments


class HybridPSOAlgorithmArguments(AlgorithmArguments):
    """Arguments for Hybrid Particle Swarm Optimization (PSO) algorithm."""

    num_particles: int
    """The number of particles in the swarm."""

    inertia_weight_min: float
    """The minimum inertia weight."""

    inertia_weight_max: float
    """The maximum inertia weight."""

    cognitive_weight_min: float
    """The minimum cognitive weight."""

    cognitive_weight_max: float
    """The maximum cognitive weight."""

    social_weight_min: float
    """The minimum social weight."""

    social_weight_max: float
    """The maximum social weight."""

    max_velocities: tuple[float, float, float]
    """The maximum velocities of particle, corresponding to the axis x, y and z."""
