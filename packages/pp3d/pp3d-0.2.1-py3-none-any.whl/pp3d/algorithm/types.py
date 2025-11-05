from pydantic import BaseModel


class AlgorithmArguments(BaseModel):
    """The base class for algorithm arguments."""

    num_waypoints: int
    """The number of waypoints in the path."""

    max_iterations: int
    """The maximum number of iterations."""

    axes_min: tuple[float, float, float]
    """The minimum value of axis, which is the lower bound of the search space, corresponding to the axis x, y and z."""

    axes_max: tuple[float, float, float]
    """The maximum value of axis, which is the upper bound of the search space, corresponding to the axis x, y and z."""

    random_seed: int | None = None
    """Random seed for reproducible results. If `None`, results will be non-deterministic. Default is `None`."""

    verbose: bool = False
    """Whether to print the progress of the algorithm. Default is `False`."""
