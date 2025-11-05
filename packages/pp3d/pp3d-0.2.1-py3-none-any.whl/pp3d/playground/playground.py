from collections.abc import Callable

import numpy as np
import pandas
import streamlit as st
from scipy.ndimage import gaussian_filter

from pp3d.algorithm.genetic.types import GeneticAlgorithmArguments
from pp3d.algorithm.hybrid.pso_types import HybridPSOAlgorithmArguments
from pp3d.algorithm.pso.types import PSOAlgorithmArguments
from pp3d.algorithm.types import AlgorithmArguments
from pp3d.common import collision_detection, flight_angle_calculator, interpolate, streamlit_widgets
from pp3d.playground import (
    genetic_algorithm_playground,
    i18n,
    pso_algorithm_playground,
    pso_ga_hybrid_playground,
)
from pp3d.playground.code_template import FITNESS_FUNCTION_CODE_TEMPLATE, TERRAIN_GENERATION_CODE_TEMPLATE
from pp3d.playground.types import AlgorithmRunningResult, MultiAlgorithmFusionResult
from pp3d.visualization import plotly_utils


def _init_streamlit_session_state():
    """Initialize the session state of streamlit."""
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "en_US"
    if "run_selected_algorithm" not in st.session_state:
        st.session_state.run_selected_algorithm = False
    if "run_multiple_algorithms" not in st.session_state:
        st.session_state.run_multiple_algorithms = False


def _init_common_algorithm_arguments() -> AlgorithmArguments:
    """Initialize the common algorithm arguments.

    Returns:
        AlgorithmArguments: The common algorithm arguments.
    """
    with st.expander(label=i18n.translate("common_arguments"), expanded=False):
        num_waypoints = st.number_input(
            i18n.translate("number_of_waypoints"), key="num_waypoints", min_value=1, max_value=50, value=4, step=1
        )
        max_iterations = st.number_input(
            i18n.translate("max_iterations"), key="max_iterations", min_value=10, max_value=1000, value=100, step=10
        )
        axes_min_x = st.number_input(
            i18n.translate("axis_min_x"), key="axes_min_x", min_value=-100.0, max_value=100.0, value=0.0, step=1.0
        )
        axes_min_y = st.number_input(
            i18n.translate("axis_min_y"), key="axes_min_y", min_value=-100.0, max_value=100.0, value=0.0, step=1.0
        )
        axes_min_z = st.number_input(
            i18n.translate("axis_min_z"), key="axes_min_z", min_value=-100.0, max_value=100.0, value=0.0, step=1.0
        )
        axes_max_x = st.number_input(
            i18n.translate("axis_max_x"), key="axes_max_x", min_value=-100.0, max_value=100.0, value=100.0, step=1.0
        )
        axes_max_y = st.number_input(
            i18n.translate("axis_max_y"), key="axes_max_y", min_value=-100.0, max_value=100.0, value=100.0, step=1.0
        )
        axes_max_z = st.number_input(
            i18n.translate("axis_max_z"), key="axes_max_z", min_value=-100.0, max_value=100.0, value=100.0, step=1.0
        )
        random_seed = st.number_input(
            i18n.translate("random_seed"),
            key="random_seed",
            min_value=0,
            max_value=1000,
            value=0,
            step=1,
        )
        verbose = st.checkbox(i18n.translate("verbose"), key="verbose")
        return AlgorithmArguments(
            num_waypoints=num_waypoints,
            max_iterations=max_iterations,
            axes_min=(axes_min_x, axes_min_y, axes_min_z),
            axes_max=(axes_max_x, axes_max_y, axes_max_z),
            random_seed=random_seed if random_seed != 0 else None,
            verbose=verbose,
        )


class Playground:
    """A class for the 3D Path Planning Playground."""

    def __init__(self):
        """Initialize the 3D Path Planning Playground."""
        st.set_page_config(page_title="3D Path Planning Playground", page_icon="🚢", layout="wide")
        self.left, self.middle, self.right = st.columns([2, 4, 4])

        self.selected_algorithm: str = "pso_algorithm"
        self.selected_algorithm_args: (
            PSOAlgorithmArguments | GeneticAlgorithmArguments | HybridPSOAlgorithmArguments | None
        ) = None
        self.input_terrain_generation_code: str = TERRAIN_GENERATION_CODE_TEMPLATE
        self.input_fitness_function_code: str = FITNESS_FUNCTION_CODE_TEMPLATE

        _init_streamlit_session_state()
        self._init_left_column()
        self._init_middle_column()
        self._init_right_column()

    def _init_left_column(self) -> None:
        """Initialize the left column of the 3D Path Planning Playground."""
        with self.left:
            st.session_state.selected_language = streamlit_widgets.select_language()

            st.header(f"⚙️ {i18n.translate('settings')}")
            self.selected_algorithm = streamlit_widgets.select_algorithm()
            self.number_of_algorithm_runs = st.number_input(
                label=i18n.translate("number_of_algorithm_runs"), min_value=1, max_value=1000, value=100, step=100
            )
            common_algorithm_args = _init_common_algorithm_arguments()

            if self.selected_algorithm == "pso_algorithm":
                self.selected_algorithm_args = pso_algorithm_playground.init_algorithm_args(common_algorithm_args)
            elif self.selected_algorithm == "genetic_algorithm":
                self.selected_algorithm_args = genetic_algorithm_playground.init_algorithm_args(common_algorithm_args)
            elif self.selected_algorithm == "pso_ga_hybrid_algorithm":
                self.selected_algorithm_args = pso_ga_hybrid_playground.init_algorithm_args(common_algorithm_args)

    def _init_middle_column(self) -> None:
        """Initialize the middle column of the 3D Path Planning Playground."""
        with self.middle:
            st.header(f"💻 {i18n.translate('code_editor')}")

            with st.expander(label=i18n.translate("terrain_generation_function"), expanded=False):
                self.input_terrain_generation_code = streamlit_widgets.code_editor(
                    value=TERRAIN_GENERATION_CODE_TEMPLATE, height=640
                )

            with st.expander(label=i18n.translate("algorithm_fitness_function"), expanded=False):
                self.input_fitness_function_code = streamlit_widgets.code_editor(
                    value=FITNESS_FUNCTION_CODE_TEMPLATE, height=640
                )

            btn_run_selected_algorithm_clicked = st.button(label=f"▶️ {i18n.translate('run_selected_algorithm')}")
            if btn_run_selected_algorithm_clicked:
                st.session_state.run_selected_algorithm = True

            btn_run_multiple_algorithms_clicked = st.button(label=f"🔄 {i18n.translate('run_multiple_algorithms')}")
            if btn_run_multiple_algorithms_clicked:
                st.session_state.run_multiple_algorithms = True

    def _init_right_column(self) -> None:
        """Initialize the right column of the 3D Path Planning Playground."""
        with self.right:
            st.header(f"📊 {i18n.translate('result_visualization')}")
            with st.spinner(text=f"{i18n.translate('running_algorithm')}...", show_time=True):
                if st.session_state.run_selected_algorithm:
                    self._run_selected_algorithm()
                if st.session_state.run_multiple_algorithms:
                    self._run_multiple_algorithms()

    def _parse_fitness_function(
        self, start_point: np.ndarray, destination: np.ndarray, xx: np.ndarray, yy: np.ndarray, zz: np.ndarray
    ) -> Callable[[np.ndarray], float] | None:
        """Parse the input fitness function code to a function.

        Args:
            start_point (np.ndarray): The start point of the path.
            destination (np.ndarray): The destination point of the path.
            xx (np.ndarray): The x coordinates of the terrain height map.
            yy (np.ndarray): The y coordinates of the terrain height map.
            zz (np.ndarray): The z coordinates of the terrain height map.

        Returns:
            Callable[[np.ndarray], float] | None: The parsed fitness function.
        """
        try:
            allowed_packages = {
                "np": np,
                "xx": xx,
                "yy": yy,
                "zz": zz,
                "interpolate": interpolate,
                "start_point": start_point,
                "destination": destination,
                "collision_detection": collision_detection,
                "flight_angle_calculator": flight_angle_calculator,
            }
            parsed_fitness_function = {}
            exec(self.input_fitness_function_code, allowed_packages, parsed_fitness_function)
            callable_fitness_function = parsed_fitness_function["fitness_function"]
            return callable_fitness_function
        except Exception as e:
            st.error(f"Error parsing fitness function code: {e}")
            return None

    def _parse_terrain_generation_function(self) -> Callable[[np.ndarray, np.ndarray], np.ndarray] | None:
        """Parse the input terrain generation function code to a function."""
        try:
            allowed_packages = {"np": np, "gaussian_filter": gaussian_filter}
            parsed_terrain_generation_function = {}
            exec(self.input_terrain_generation_code, allowed_packages, parsed_terrain_generation_function)
            callable_terrain_generation_function = parsed_terrain_generation_function["generate_terrain"]
            return callable_terrain_generation_function
        except Exception as e:
            st.error(f"Error parsing terrain generation code: {e}")

    def _generate_terrain(
        self, axes_min: tuple[float, float, float], axes_max: tuple[float, float, float]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate the terrain using the input terrain generation function code.

        Args:
            axes_min (tuple[float, float, float]): The minimum values of the axes.
            axes_max (tuple[float, float, float]): The maximum values of the axes.

        Returns:
            xx (np.ndarray): The x-axis values of the terrain.
            yy (np.ndarray): The y-axis values of the terrain.
            zz (np.ndarray): The z-axis values of the terrain.
        """
        callable_terrain_generation_function = self._parse_terrain_generation_function()

        if callable_terrain_generation_function is None:
            st.error("Error running algorithm: callable_terrain_generation_function is None.")
            return np.array([]), np.array([]), np.array([])

        x = np.linspace(start=axes_min[0], stop=axes_max[0], num=100)
        y = np.linspace(start=axes_min[1], stop=axes_max[1], num=100)
        xx, yy = np.meshgrid(x, y)

        zz = callable_terrain_generation_function(xx, yy)

        return xx, yy, zz

    def _run_selected_algorithm(self) -> None:
        """Run the selected algorithm."""
        st.session_state.run_selected_algorithm = False

        if self.selected_algorithm_args is None:
            st.error("Error running algorithm: self.selected_algorithm_args is None.")
            return

        start_point = np.array([0, 0, 5])
        destination = np.array([90, 90, 5])

        axes_min = self.selected_algorithm_args.axes_min
        axes_max = self.selected_algorithm_args.axes_max
        xx, yy, zz = self._generate_terrain(axes_min, axes_max)

        callable_fitness_function = self._parse_fitness_function(start_point, destination, xx, yy, zz)

        if callable_fitness_function is None:
            st.error("Error running algorithm: callable_fitness_function is None.")
            return

        args = self.selected_algorithm_args
        running_result = AlgorithmRunningResult(
            best_path_points=np.array([]),
            best_fitness_values=[],
            best_fitness_value_samples=[],
            running_time_samples=[],
        )

        if self.selected_algorithm == "pso_algorithm" and isinstance(args, PSOAlgorithmArguments):
            running_result = pso_algorithm_playground.run_algorithm(
                args, callable_fitness_function, self.number_of_algorithm_runs
            )
        elif self.selected_algorithm == "genetic_algorithm" and isinstance(args, GeneticAlgorithmArguments):
            running_result = genetic_algorithm_playground.run_algorithm(
                args, callable_fitness_function, self.number_of_algorithm_runs
            )
        elif self.selected_algorithm == "pso_ga_hybrid_algorithm" and isinstance(args, HybridPSOAlgorithmArguments):
            running_result = pso_ga_hybrid_playground.run_algorithm(
                args, callable_fitness_function, self.number_of_algorithm_runs
            )

        # Only plot the fitness curve and path when times is 1.
        if self.number_of_algorithm_runs == 1:
            best_path_points = running_result.best_path_points
            best_fitness_values = running_result.best_fitness_values
            full_path_points = np.vstack([start_point, best_path_points, destination])
            plotly_utils.plot_terrain_and_path(xx, yy, zz, start_point, destination, full_path_points)
            plotly_utils.plot_line_chart(
                values=best_fitness_values,
                title=i18n.translate("fitness_curve"),
                xaxis_title=i18n.translate("iterations"),
                yaxis_title=i18n.translate("fitness"),
            )
        else:  # otherwise, show the table of fitness value samples and running time samples
            best_fitness_value_samples = running_result.best_fitness_value_samples
            running_time_samples = running_result.running_time_samples
            table_data = pandas.DataFrame(
                data={
                    i18n.translate("max"): [np.max(best_fitness_value_samples), np.max(running_time_samples)],
                    i18n.translate("min"): [np.min(best_fitness_value_samples), np.min(running_time_samples)],
                    i18n.translate("avg"): [np.mean(best_fitness_value_samples), np.mean(running_time_samples)],
                    i18n.translate("std"): [
                        np.std(best_fitness_value_samples, ddof=1),
                        np.std(running_time_samples, ddof=1),
                    ],
                },
                index=[i18n.translate("best_fitness_value_samples"), i18n.translate("running_time_samples")],
            )
            st.table(table_data.style.format(precision=6))

    def _run_multiple_algorithms(self) -> None:
        """Run multiple algorithms."""
        st.session_state.run_multiple_algorithms = False

        start_point = np.array([0, 0, 5])
        destination = np.array([90, 90, 5])

        num_particles = 50
        num_waypoints = 4
        max_iterations = 300
        axes_min = (0, 0, 0)
        axes_max = (100, 100, 100)
        max_velocities = (1.0, 1.0, 1.0)

        pso_algorithm_args = PSOAlgorithmArguments(
            num_particles=num_particles,
            num_waypoints=num_waypoints,
            max_iterations=max_iterations,
            inertia_weight=0.4,
            cognitive_weight=1.5,
            social_weight=1.5,
            max_velocities=max_velocities,
            axes_min=axes_min,
            axes_max=axes_max,
            random_seed=None,
            verbose=False,
        )
        ga_algorithm_args = GeneticAlgorithmArguments(
            population_size=num_particles,
            tournament_size=3,
            num_waypoints=num_waypoints,
            max_iterations=max_iterations,
            crossover_rate=0.8,
            mutation_rate=0.2,
            axes_min=axes_min,
            axes_max=axes_max,
            random_seed=None,
            verbose=False,
        )
        pso_ga_hybrid_algorithm_args = HybridPSOAlgorithmArguments(
            num_particles=num_particles,
            num_waypoints=num_waypoints,
            max_iterations=max_iterations,
            inertia_weight_min=0.4,
            inertia_weight_max=0.9,
            cognitive_weight_min=0.5,
            cognitive_weight_max=2.5,
            social_weight_min=0.5,
            social_weight_max=2.5,
            max_velocities=max_velocities,
            axes_min=axes_min,
            axes_max=axes_max,
            random_seed=None,
            verbose=False,
        )

        # All algorithms use the same terrain, so we only need to generate the terrain once.
        xx, yy, zz = self._generate_terrain(pso_algorithm_args.axes_min, pso_algorithm_args.axes_max)

        callable_fitness_function = self._parse_fitness_function(start_point, destination, xx, yy, zz)

        if callable_fitness_function is None:
            st.error("Error running algorithm: callable_fitness_function is None.")
            return

        pso_algorithm_result = pso_algorithm_playground.run_algorithm(pso_algorithm_args, callable_fitness_function)
        ga_algorithm_result = genetic_algorithm_playground.run_algorithm(ga_algorithm_args, callable_fitness_function)
        pso_ga_hybrid_algorithm_result = pso_ga_hybrid_playground.run_algorithm(
            pso_ga_hybrid_algorithm_args, callable_fitness_function
        )

        multi_algorithm_fusion_result = MultiAlgorithmFusionResult(
            pso_full_path_points=np.vstack([start_point, pso_algorithm_result.best_path_points, destination]),
            ga_full_path_points=np.vstack([start_point, ga_algorithm_result.best_path_points, destination]),
            pso_ga_hybrid_full_path_points=np.vstack(
                [start_point, pso_ga_hybrid_algorithm_result.best_path_points, destination]
            ),
            pso_best_fitness_values=pso_algorithm_result.best_fitness_values,
            ga_best_fitness_values=ga_algorithm_result.best_fitness_values,
            pso_ga_hybrid_best_fitness_values=pso_ga_hybrid_algorithm_result.best_fitness_values,
        )

        pso_result_table_data = pandas.DataFrame(
            data={
                "Best Fitness Value": [pso_algorithm_result.best_fitness_values[-1]],
                "Particles": [pso_algorithm_args.num_particles],
                "Waypoints": [pso_algorithm_args.num_waypoints],
                "Max Iterations": [pso_algorithm_args.max_iterations],
                "Inertia Weight": [pso_algorithm_args.inertia_weight],
                "Cognitive Weight": [pso_algorithm_args.cognitive_weight],
                "Social Weight": [pso_algorithm_args.social_weight],
            },
            index=["PSO"],
        )
        st.table(pso_result_table_data.style.format(precision=6))

        ga_result_table_data = pandas.DataFrame(
            data={
                "Best Fitness Value": [ga_algorithm_result.best_fitness_values[-1]],
                "Population Size": [ga_algorithm_args.population_size],
                "Tournament Size": [ga_algorithm_args.tournament_size],
                "Waypoints": [ga_algorithm_args.num_waypoints],
                "Max Iterations": [ga_algorithm_args.max_iterations],
                "Crossover Rate": [ga_algorithm_args.crossover_rate],
                "Mutation Rate": [ga_algorithm_args.mutation_rate],
            },
            index=["GA"],
        )
        st.table(ga_result_table_data.style.format(precision=6))

        pso_ga_hybrid_result_table_data = pandas.DataFrame(
            data={
                "Best Fitness Value": [pso_ga_hybrid_algorithm_result.best_fitness_values[-1]],
                "Particles": [pso_ga_hybrid_algorithm_args.num_particles],
                "Waypoints": [pso_ga_hybrid_algorithm_args.num_waypoints],
                "Max Iterations": [pso_ga_hybrid_algorithm_args.max_iterations],
                "Min Inertia Weight": [pso_ga_hybrid_algorithm_args.inertia_weight_min],
                "Max Inertia Weight": [pso_ga_hybrid_algorithm_args.inertia_weight_max],
                "Min Cognitive Weight": [pso_ga_hybrid_algorithm_args.cognitive_weight_min],
                "Max Cognitive Weight": [pso_ga_hybrid_algorithm_args.cognitive_weight_max],
                "Min Social Weight": [pso_ga_hybrid_algorithm_args.social_weight_min],
                "Max Social Weight": [pso_ga_hybrid_algorithm_args.social_weight_max],
            },
            index=["PSO-GA Hybrid"],
        )
        st.table(pso_ga_hybrid_result_table_data.style.format(precision=6))

        plotly_utils.plot_terrain_and_multipath(xx, yy, zz, start_point, destination, multi_algorithm_fusion_result)
        plotly_utils.plot_multiple_fitness_curves(multi_algorithm_fusion_result)


if __name__ == "__main__":
    Playground()
