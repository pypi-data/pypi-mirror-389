from pp3d.common.types import ProblemType


def compare_fitness(fitness1: float, fitness2: float, problem_type: ProblemType) -> bool:
    """Compare two fitness values by the problem type.

    Args:
        fitness1 (float): The fitness value.
        fitness2 (float): The another fitness value.
        problem_type (ProblemType): The type of the problem.

    Returns:
        bool: True if fitness1 is better than fitness2, False otherwise.
    """
    return fitness1 < fitness2 if problem_type == ProblemType.MINIMIZATION else fitness1 > fitness2
