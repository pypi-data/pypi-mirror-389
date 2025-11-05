from enum import Enum, unique


@unique
class ProblemType(Enum):
    """The type of the problem to be solved."""

    MINIMIZATION = 1
    """The problem is a minimization problem."""

    MAXIMIZATION = 2
    """The problem is a maximization problem."""
