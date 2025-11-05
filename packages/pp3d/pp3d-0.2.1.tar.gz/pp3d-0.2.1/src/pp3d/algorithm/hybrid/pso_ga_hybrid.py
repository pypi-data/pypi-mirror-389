import sys
from collections.abc import Callable

import numpy as np
from loguru import logger

from pp3d.algorithm.hybrid.pso_types import HybridPSOAlgorithmArguments
from pp3d.algorithm.pso.types import Particle
from pp3d.common import algorithm_utils
from pp3d.common.decorators import timer
from pp3d.common.types import ProblemType


class HybridPSOAlgorithm:
    """Hybrid Particle Swarm Optimization (PSO) algorithm."""

    def __init__(
        self,
        args: HybridPSOAlgorithmArguments,
        fitness_function: Callable[[np.ndarray], float],
        problem_type: ProblemType = ProblemType.MINIMIZATION,
    ) -> None:
        """Initialize the Hybrid PSO algorithm.

        Args:
            args (HybridPSOAlgorithmArguments): The arguments of the Hybrid PSO algorithm.
            fitness_function (Callable[[np.ndarray], float]): The fitness function.
            problem_type (ProblemType): The type of the problem. Defaults to ProblemType.MINIMIZATION.
        """
        logger.remove()
        logger.add(sink=sys.stdout, level="DEBUG" if args.verbose else "INFO")

        logger.info("Initialize Hybrid PSO algorithm with arguments: {}", args.model_dump_json())

        if args.random_seed is not None and args.random_seed > 0:
            np.random.seed(args.random_seed)
            logger.debug(f"Random seed is set to {args.random_seed}")

        self.args = args
        self.fitness_function = fitness_function
        self.problem_type = problem_type
        self.axes_min = np.array(args.axes_min)
        self.axes_max = np.array(args.axes_max)
        self.max_velocities = np.array(args.max_velocities)
        self.shape = (args.num_waypoints, len(args.axes_min))

        self._init_particle_swarm()

        logger.success("Hybrid PSO algorithm initialized successfully")

    def _init_particle_swarm(self) -> None:
        """Initialize the particles swarm."""
        logger.debug(f"Initializing {self.args.num_particles} particles and the global best solution...")

        # Initialize particles
        self.particles: list[Particle] = []
        initial_fitness_value = np.inf if self.problem_type == ProblemType.MINIMIZATION else -np.inf

        for _ in range(self.args.num_particles):
            initial_position = np.random.uniform(self.axes_min, self.axes_max, self.shape).flatten()
            initial_velocity = np.random.uniform(-self.max_velocities, self.max_velocities, self.shape).flatten()
            particle = Particle(
                position=initial_position,
                velocity=initial_velocity,
                best_position=initial_position.copy(),
                best_fitness_value=initial_fitness_value,
            )
            self.particles.append(particle)

        # Initialize global best position and fitness value
        logger.debug("Evaluating fitness values of particles for the first time...")

        fitness_values = [self.fitness_function(particle.position) for particle in self.particles]
        arg_func = np.argmin if self.problem_type == ProblemType.MINIMIZATION else np.argmax
        value_func = np.min if self.problem_type == ProblemType.MINIMIZATION else np.max

        best_particle_index = arg_func(fitness_values)
        self.global_best_position = self.particles[best_particle_index].position.copy()
        self.global_best_fitness_value = value_func(fitness_values)
        logger.debug(f"Evaluated global best position: {self.global_best_position}")
        logger.debug(f"Evaluated global best fitness value: {self.global_best_fitness_value}")

    def _get_inertia_weight(self, current_iteration: int) -> float:
        """Get the inertia weight for the current iteration.

        Args:
            current_iteration (int): The current iteration of the algorithm.

        Returns:
            float: The inertia weight for the current iteration.
        """
        # Use linearly decreasing inertia weight
        inertia_weight = self.args.inertia_weight_max - (
            self.args.inertia_weight_max - self.args.inertia_weight_min
        ) * (current_iteration / self.args.max_iterations)
        logger.debug(f"Iteration {current_iteration}/{self.args.max_iterations}, inertia_weight = {inertia_weight}")
        return inertia_weight

    def _get_cognitive_weight(self, current_iteration: int) -> float:
        """Get the cognitive weight for the current iteration.

        Args:
            current_iteration (int): The current iteration of the algorithm.

        Returns:
            float: The cognitive weight for the current iteration.
        """
        # Use linearly decreasing cognitive weight
        cognitive_weight = self.args.cognitive_weight_max - (
            self.args.cognitive_weight_max - self.args.cognitive_weight_min
        ) * (current_iteration / self.args.max_iterations)
        logger.debug(f"Iteration {current_iteration}/{self.args.max_iterations}, cognitive_weight = {cognitive_weight}")
        return cognitive_weight

    def _get_social_weight(self, current_iteration: int) -> float:
        """Get the social weight for the current iteration.

        Args:
            current_iteration (int): The current iteration of the algorithm.

        Returns:
            float: The social weight for the current iteration.
        """
        # Use linearly increasing social weight
        social_weight = self.args.social_weight_min + (self.args.social_weight_max - self.args.social_weight_min) * (
            current_iteration / self.args.max_iterations
        )
        logger.debug(f"Iteration {current_iteration}/{self.args.max_iterations}, social_weight = {social_weight}")
        return social_weight

    def _update_particle_velocities_and_positions(self, current_iteration: int) -> None:
        """Update the velocities and positions of the particles.

        Args:
            current_iteration (int): The current iteration of the algorithm.
        """
        logger.debug(f"Updating particle velocities and positions for iteration {current_iteration}...")

        inertia_weight = self._get_inertia_weight(current_iteration)
        cognitive_weight = self._get_cognitive_weight(current_iteration)
        social_weight = self._get_social_weight(current_iteration)

        for particle in self.particles:
            r1 = np.random.rand(self.shape[0], self.shape[1]).flatten()
            r2 = np.random.rand(self.shape[0], self.shape[1]).flatten()

            # Update velocity
            cognitive_velocity = cognitive_weight * r1 * (particle.best_position - particle.position)
            social_velocity = social_weight * r2 * (self.global_best_position - particle.position)
            particle.velocity = inertia_weight * particle.velocity + cognitive_velocity + social_velocity
            # Clip velocity
            reshaped_velocity = particle.velocity.reshape(self.shape)
            particle.velocity = np.clip(reshaped_velocity, -self.max_velocities, self.max_velocities).flatten()

            # Update position
            particle.position += particle.velocity
            # Clip position
            reshaped_position = particle.position.reshape(self.shape)
            particle.position = np.clip(reshaped_position, self.axes_min, self.axes_max).flatten()

    def _update_best_solutions(self, current_iteration: int) -> None:
        """Update the individual and global best solutions.

        Args:
            current_iteration (int): The current iteration of the algorithm.
        """
        logger.debug(f"Updating individual and global best solutions for iteration {current_iteration}...")

        fitness_values = [self.fitness_function(particle.position) for particle in self.particles]

        for i, particle in enumerate(self.particles):
            # Update individual best position and fitness value
            if algorithm_utils.compare_fitness(fitness_values[i], particle.best_fitness_value, self.problem_type):
                logger.debug(f"Particle {i + 1} updated its best position and fitness value")
                particle.best_fitness_value = fitness_values[i]
                particle.best_position = particle.position.copy()

            # Update global best position and fitness value
            if algorithm_utils.compare_fitness(fitness_values[i], self.global_best_fitness_value, self.problem_type):
                logger.debug(f"Particle {i + 1} updated the global best position and fitness value")
                self.global_best_fitness_value = fitness_values[i]
                self.global_best_position = particle.position.copy()

    def _use_genetic_algorithm_to_optimize_pso(self, current_iteration: int) -> None:
        """Use genetic algorithm to collaboratively optimize PSO algorithm.

        Args:
            current_iteration (int): The current iteration of the algorithm.
        """
        logger.info("Use genetic algorithm to optimize PSO algorithm")

        fitness_values = np.array([p.best_fitness_value for p in self.particles])
        sorted_indices_by_fitness = (
            np.argsort(fitness_values)
            if self.problem_type == ProblemType.MINIMIZATION
            else np.argsort(fitness_values)[::-1]
        )

        # Select the top 50% particles to be used in the genetic algorithm
        top_particles = [self.particles[i] for i in sorted_indices_by_fitness[: len(sorted_indices_by_fitness) // 2]]

        # Use genetic algorithm to mutate the top 50% particles
        mutated_particles: list[Particle] = []
        for i in range(0, len(top_particles) - 1, 2):
            parent1, parent2 = top_particles[i], top_particles[i + 1]
            child1, child2 = self._crossover(parent1, parent2, current_iteration)
            mutated_child1 = self._mutate(child1, current_iteration)
            mutated_child2 = self._mutate(child2, current_iteration)
            mutated_particles.append(mutated_child1)
            mutated_particles.append(mutated_child2)

        # Replace the bottom 50% particles with the mutated particles
        worst_indices = sorted_indices_by_fitness[-len(mutated_particles) :]
        for i, particle in zip(worst_indices, mutated_particles):
            self.particles[i].position = particle.position.copy()
            self.particles[i].best_position = particle.position.copy()

    def _crossover(self, parent1: Particle, parent2: Particle, current_iteration: int) -> tuple[Particle, Particle]:
        """Crossover the parents to generate children.

        Args:
            parent1 (Particle): The first parent.
            parent2 (Particle): The second parent.
            current_iteration (int): The current iteration of the genetic algorithm.

        Returns:
            tuple[Particle, Particle]: The parents with new position.
        """
        logger.debug("Use genetic algorithm to crossover particles")

        # Dynamic crossover rate
        sin_coefficient = 0.5
        golden_ratio = (1 + np.sqrt(5)) / 2
        crossover_rate_decay = 0.01
        static_crossover_rate = 0.8
        dynamic_crossover_rate = (
            sin_coefficient
            * (1 + np.sin(2 * np.pi * static_crossover_rate / (1 + golden_ratio)))
            * np.exp(-crossover_rate_decay * current_iteration)
        )

        # Dynamic crossover parameter
        particle_distribution_coefficient_eta = 2 * (1 + 0.2 * np.cos(2 * np.pi * current_iteration / 15))
        power = 1 / (particle_distribution_coefficient_eta + 1)
        random_num = np.random.rand()
        if random_num <= 0.5:
            crossover_parameter_beta = np.power(2 * random_num, power)
        else:
            crossover_parameter_beta = np.power(1 / (2 - 2 * random_num), power)

        # Simulated binary crossover
        child1_position = dynamic_crossover_rate * parent1.position + (1 - dynamic_crossover_rate) * parent2.position
        child2_position = dynamic_crossover_rate * parent2.position + (1 - dynamic_crossover_rate) * parent1.position

        # Add standard t-distribution perturbation to children
        standard_t_value = np.random.standard_t(df=3, size=parent1.position.shape)
        child1_position = (
            0.5 * ((1 + crossover_parameter_beta) * child1_position + (1 - crossover_parameter_beta) * child2_position)
            + 2 * standard_t_value
        )
        child2_position = (
            0.5 * ((1 + crossover_parameter_beta) * child2_position + (1 - crossover_parameter_beta) * child1_position)
            + 2 * standard_t_value
        )

        # Clip children to ensure they are within the search space
        child1_position = np.clip(child1_position.reshape(self.shape), self.axes_min, self.axes_max).flatten()
        child2_position = np.clip(child2_position.reshape(self.shape), self.axes_min, self.axes_max).flatten()

        parent1.position = child1_position.copy()
        parent1.best_position = child1_position.copy()
        parent2.position = child2_position.copy()
        parent2.best_position = child2_position.copy()

        return parent1, parent2

    def _mutate(self, particle: Particle, current_iteration: int) -> Particle:
        """Mutate the particle.

        Args:
            particle (Particle): The particle to mutate.
            current_iteration (int): The current iteration of the algorithm.

        Returns:
            Particle: The mutated particle.
        """
        logger.debug("Use genetic algorithm to mutate particle")

        # Dynamic mutation rate
        sin_coefficient = 0.5
        golden_ratio = (1 + np.sqrt(5)) / 2
        mutation_rate_decay = 0.01
        static_mutation_rate = 0.2
        dynamic_mutation_rate = (
            sin_coefficient
            * (1 + np.sin(2 * np.pi * static_mutation_rate / (1 + golden_ratio)))
            * np.exp(-mutation_rate_decay * current_iteration)
        )

        # Calculate levy flight step size
        gaussian_distribution_random_num_u = np.random.normal(loc=0, scale=1, size=particle.position.shape)
        gaussian_distribution_random_num_v = np.random.normal(loc=0, scale=1, size=particle.position.shape)
        random_num1 = np.random.rand()
        random_num2 = np.random.rand()
        levy_flight_alpha = max(0.6 - 0.1 * current_iteration / self.args.max_iterations, 0.5)
        levy_flight_beta = max(1.5 - 0.1 * current_iteration / self.args.max_iterations, 1)
        levy_flight_step_size = (
            gaussian_distribution_random_num_u
            / np.power(np.abs(gaussian_distribution_random_num_v), 1 / levy_flight_beta)
            * levy_flight_alpha
            * random_num1
            * np.power(np.abs(random_num2), 1 / levy_flight_beta)
        )

        mutated_position = particle.position + dynamic_mutation_rate * levy_flight_step_size

        # Clip mutated position to ensure it is within the search space
        mutated_position = np.clip(mutated_position.reshape(self.shape), self.axes_min, self.axes_max).flatten()

        particle.position = mutated_position.copy()
        particle.best_position = mutated_position.copy()

        return particle

    @timer
    def run(self) -> tuple[np.ndarray, list[float]]:
        """Run the Hybrid PSO algorithm.

        Returns:
            tuple[np.ndarray, list[float]]: The best path points and fitness values.
        """
        logger.info("Running Hybrid PSO algorithm...")

        # Collect the best fitness value of each iteration for fitness curve visualization
        best_fitness_values: list[float] = []

        for iteration in range(self.args.max_iterations):
            self._update_particle_velocities_and_positions(iteration + 1)
            self._update_best_solutions(iteration + 1)

            best_fitness_values.append(self.global_best_fitness_value)

            logger.info(
                f"Iteration {iteration + 1}/{self.args.max_iterations}, "
                f"best fitness value = {self.global_best_fitness_value:.6f}"
            )

            self._use_genetic_algorithm_to_optimize_pso(iteration + 1)

        logger.success(f"Hybrid PSO algorithm finished, best fitness value = {self.global_best_fitness_value:.6f}")

        # [x1, y1, z1, x2, y2, z2, ...] → [[x1, y1, z1], [x2, y2, z2], ...]
        best_path_points = self.global_best_position.reshape(-1, len(self.axes_min))
        return best_path_points, best_fitness_values
