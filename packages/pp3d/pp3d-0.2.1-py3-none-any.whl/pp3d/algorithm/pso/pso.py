import sys
from collections.abc import Callable

import numpy as np
from loguru import logger

from pp3d.algorithm.pso.types import Particle, PSOAlgorithmArguments
from pp3d.common import algorithm_utils
from pp3d.common.decorators import timer
from pp3d.common.types import ProblemType


class PSOAlgorithm:
    """The implementation of standard PSO (Particle Swarm Optimization) algorithm."""

    def __init__(
        self,
        args: PSOAlgorithmArguments,
        fitness_function: Callable[[np.ndarray], float],
        problem_type: ProblemType = ProblemType.MINIMIZATION,
    ) -> None:
        """Initialize the PSO algorithm.

        Args:
            args (PSOAlgorithmArguments): The arguments of the algorithm.
            fitness_function (Callable[[np.ndarray], float]): The fitness function.
            problem_type (ProblemType): The type of the problem. Defaults to ProblemType.MINIMIZATION.
        """
        logger.remove()
        logger.add(sink=sys.stdout, level="DEBUG" if args.verbose else "INFO")

        logger.info("Initialize PSO algorithm with arguments: {}", args.model_dump_json())

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

        logger.success("PSO algorithm initialized successfully")

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

    def _get_inertia_weight(self) -> float:
        """Get the inertia weight for the current iteration.

        Returns:
            float: The inertia weight for the current iteration.
        """
        return self.args.inertia_weight

    def _get_cognitive_weight(self) -> float:
        """Get the cognitive weight for the current iteration.

        Returns:
            float: The cognitive weight for the current iteration.
        """
        return self.args.cognitive_weight

    def _get_social_weight(self) -> float:
        """Get the social weight for the current iteration.

        Returns:
            float: The social weight for the current iteration.
        """
        return self.args.social_weight

    def _update_particle_velocities_and_positions(self, current_iteration: int) -> None:
        """Update the velocities and positions of the particles.

        Args:
            current_iteration (int): The current iteration of the algorithm.
        """
        logger.debug(f"Updating particle velocities and positions for iteration {current_iteration}...")

        inertia_weight = self._get_inertia_weight()
        cognitive_weight = self._get_cognitive_weight()
        social_weight = self._get_social_weight()

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

    @timer
    def run(self) -> tuple[np.ndarray, list[float]]:
        """Run the PSO algorithm.

        Returns:
            tuple[np.ndarray, list[float]]: The best path points and fitness values.
        """
        logger.info("Running PSO algorithm...")

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

        logger.success(f"PSO algorithm finished, best fitness value = {self.global_best_fitness_value:.6f}")

        # [x1, y1, z1, x2, y2, z2, ...] → [[x1, y1, z1], [x2, y2, z2], ...]
        best_path_points = self.global_best_position.reshape(-1, len(self.axes_min))
        return best_path_points, best_fitness_values
