import sys
from collections.abc import Callable

import numpy as np
from loguru import logger

from pp3d.algorithm.genetic.types import GeneticAlgorithmArguments, Individual
from pp3d.common import algorithm_utils
from pp3d.common.decorators import timer
from pp3d.common.types import ProblemType


class GeneticAlgorithm:
    """The implementation of standard genetic algorithm."""

    def __init__(
        self,
        args: GeneticAlgorithmArguments,
        fitness_function: Callable[[np.ndarray], float],
        problem_type: ProblemType = ProblemType.MINIMIZATION,
    ) -> None:
        """Initialize the genetic algorithm.

        Args:
            args (GeneticAlgorithmArguments): The arguments of the algorithm.
            fitness_function (Callable[[np.ndarray], float]): The fitness function.
            problem_type (ProblemType): The type of the problem. Defaults to ProblemType.MINIMIZATION.
        """
        logger.remove()
        logger.add(sink=sys.stdout, level="DEBUG" if args.verbose else "INFO")

        logger.info("Initialize genetic algorithm with arguments: {}", args.model_dump_json())

        if args.random_seed is not None and args.random_seed > 0:
            np.random.seed(args.random_seed)
            logger.debug(f"Random seed is set to {args.random_seed}")

        if args.population_size % 2 != 0:
            args.population_size += 1
            logger.warning(f"Population size is set to {args.population_size} to be even")

        self.args = args
        self.fitness_function = fitness_function
        self.problem_type = problem_type
        self.axes_min = np.array(args.axes_min)
        self.axes_max = np.array(args.axes_max)
        self.shape = (args.num_waypoints, len(args.axes_min))
        self.num_genes = args.num_waypoints * len(args.axes_min)
        self.initial_fitness_value = np.inf if self.problem_type == ProblemType.MINIMIZATION else -np.inf

        self.population = self._init_population()

        logger.success("Genetic algorithm initialized successfully")

    def _init_population(self) -> list[Individual]:
        """Initialize the population.

        Returns:
            list[Individual]: The initialized population.
        """
        logger.debug(f"Initializing {self.args.population_size} individuals...")

        population: list[Individual] = []

        for i in range(self.args.population_size):
            gene = np.random.uniform(self.axes_min, self.axes_max, self.shape).flatten()
            individual = Individual(gene=gene, fitness_value=self.initial_fitness_value)
            population.append(individual)

        self.best_individual: Individual = population[0]

        return population

    def _evaluate_fitness(self) -> np.ndarray:
        """Evaluate the fitness of the population.

        Returns:
            np.ndarray: The fitness values of the individuals.
        """
        fitness_values = np.array([self.fitness_function(individual.gene) for individual in self.population])
        return fitness_values

    def _select(self, fitness_values: np.ndarray) -> list[Individual]:
        """Select the parents for the next generation.

        Args:
            fitness_values (np.ndarray): The fitness values of the individuals.

        Returns:
            list[Individual]: The selected parents.
        """
        selected_parents: list[Individual] = []
        while len(selected_parents) < self.args.population_size:
            tournament_indices = np.random.choice(len(self.population), size=self.args.tournament_size, replace=False)
            tournament_fitness_values = fitness_values[tournament_indices]
            arg_func = np.argmin if self.problem_type == ProblemType.MINIMIZATION else np.argmax
            winner_index = tournament_indices[arg_func(tournament_fitness_values)]
            selected_parents.append(self.population[winner_index])
        return selected_parents

    def _crossover(self, parent1: Individual, parent2: Individual) -> tuple[Individual, Individual]:
        """Crossover the parents to generate children.

        Args:
            parent1 (Individual): The first parent.
            parent2 (Individual): The second parent.

        Returns:
            tuple[Individual, Individual]: The children or parents themselves.
        """
        if np.random.rand() < self.args.crossover_rate:
            alpha = np.random.rand(self.num_genes)
            child1_gene = alpha * parent1.gene + (1 - alpha) * parent2.gene
            child2_gene = (1 - alpha) * parent1.gene + alpha * parent2.gene
            child1 = Individual(gene=child1_gene, fitness_value=self.initial_fitness_value)
            child2 = Individual(gene=child2_gene, fitness_value=self.initial_fitness_value)
            return child1, child2
        else:
            return parent1, parent2

    def _mutate(self, individual: Individual, current_iteration: int) -> Individual:
        """Mutate the individual.

        Args:
            individual (Individual): The individual to mutate.
            current_iteration (int): The current iteration of the algorithm.

        Returns:
            Individual: The mutated individual or individual itself.
        """
        if np.random.rand() < self.args.mutation_rate:
            mutation_strength = 0.5 * (1 - current_iteration / self.args.max_iterations)
            noise = np.random.normal(loc=0, scale=mutation_strength, size=self.num_genes)
            mutated_and_reshaped_gene = (individual.gene + noise).reshape(self.shape)
            mutated_gene = np.clip(mutated_and_reshaped_gene, self.axes_min, self.axes_max).flatten()
            return Individual(gene=mutated_gene, fitness_value=self.initial_fitness_value)
        return individual

    def _update_best_solution(self, fitness_values: np.ndarray) -> None:
        """Update the best solution.

        Args:
            fitness_values (np.ndarray): The fitness values of the individuals.
        """
        arg_func = np.argmin if self.problem_type == ProblemType.MINIMIZATION else np.argmax
        best_individual_index = arg_func(fitness_values)

        best_fitness_value = fitness_values[best_individual_index].item()
        best_individual = self.population[best_individual_index]
        best_individual.fitness_value = best_fitness_value

        if algorithm_utils.compare_fitness(best_fitness_value, self.best_individual.fitness_value, self.problem_type):
            self.best_individual = best_individual

    @timer
    def run(self) -> tuple[np.ndarray, list[float]]:
        """Run the genetic algorithm.

        Returns:
            tuple[np.ndarray, list[float]]: The best path points and fitness values.
        """
        # Collect the best fitness value of each iteration for fitness curve visualization
        best_fitness_values: list[float] = []

        for iteration in range(self.args.max_iterations):
            fitness_values = self._evaluate_fitness()

            self._update_best_solution(fitness_values)

            best_fitness_values.append(self.best_individual.fitness_value)
            logger.info(
                f"Iteration {iteration + 1}/{self.args.max_iterations}, "
                f"best fitness value = {self.best_individual.fitness_value:.6f}"
            )

            parents = self._select(fitness_values)

            next_population: list[Individual] = [self.best_individual]  # Elitism: preserve the best individual directly

            for i in range(0, self.args.population_size - 1, 2):
                parent1, parent2 = parents[i], parents[i + 1]
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1, iteration)
                child2 = self._mutate(child2, iteration)
                next_population.append(child1)
                next_population.append(child2)

            self.population = next_population

        logger.success(f"Genetic algorithm finished, best fitness value = {self.best_individual.fitness_value:.6f}")

        # [x1, y1, z1, x2, y2, z2, ...] → [[x1, y1, z1], [x2, y2, z2], ...]
        best_path_points = self.best_individual.gene.reshape(-1, len(self.axes_min))
        return best_path_points, best_fitness_values
