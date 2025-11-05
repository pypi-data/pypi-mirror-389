import numpy as np
import streamlit as st
from plotly import graph_objects

from pp3d.common import interpolate
from pp3d.playground import i18n
from pp3d.playground.types import MultiAlgorithmFusionResult


def _calculate_camera_eye(elev: float, azim: float, distance: float = 2.5) -> dict:
    """Calculate the camera eye position for Plotly 3D scene.

    Args:
        elev: Elevation angle in degrees.
        azim: Azimuth angle in degrees.
        distance: Distance from the camera to the scene.

    Returns:
        A dictionary with "x", "y", and "z" keys representing the camera eye position.
    """
    # Convert angles to radians
    elev_rad = np.radians(elev)
    azim_rad = np.radians(azim)

    # Calculate camera position
    x = np.cos(elev_rad) * np.cos(azim_rad) * distance
    y = np.cos(elev_rad) * np.sin(azim_rad) * distance
    z = np.sin(elev_rad) * distance
    return {"x": x, "y": y, "z": z}


def plot_line_chart(values: list[float], title: str, xaxis_title: str, yaxis_title: str) -> None:
    """Plot a line chart using Plotly.

    Args:
        values (list[float]): Values of each iteration.
        title (str): Title of the line chart.
        xaxis_title (str): Title of the x-axis.
        yaxis_title (str): Title of the y-axis.
    """
    fig = graph_objects.Figure(data=[graph_objects.Scatter(y=values)])
    fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
    st.plotly_chart(fig, width="stretch")


def plot_terrain_and_path(
    xx: np.ndarray,
    yy: np.ndarray,
    zz: np.ndarray,
    start_point: np.ndarray,
    destination: np.ndarray,
    path_points: np.ndarray,
) -> None:
    """Plot the terrain and path using Plotly.

    Args:
        xx: X coordinates of the terrain.
        yy: Y coordinates of the terrain.
        zz: Z coordinates of the terrain.
        start_point: Start point of the path.
        destination: Destination of the path.
        path_points: Path points to be plotted, shape: (n, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
    """
    terrain = graph_objects.Surface(x=xx, y=yy, z=zz, showscale=False, name=i18n.translate("terrain"))

    start_point_scatter = graph_objects.Scatter3d(
        x=[start_point[0]],
        y=[start_point[1]],
        z=[start_point[2]],
        mode="markers",
        marker={"size": 5, "color": "green"},
        name=i18n.translate("start_point"),
    )

    destination_scatter = graph_objects.Scatter3d(
        x=[destination[0]],
        y=[destination[1]],
        z=[destination[2]],
        mode="markers",
        marker={"size": 5, "color": "red"},
        name=i18n.translate("destination"),
    )

    smooth_path_points = interpolate.smooth_path_with_cubic_spline(path_points)
    smooth_x, smooth_y, smooth_z = smooth_path_points[:, 0], smooth_path_points[:, 1], smooth_path_points[:, 2]
    path = graph_objects.Scatter3d(
        x=smooth_x,
        y=smooth_y,
        z=smooth_z,
        mode="lines",
        line={"width": 6, "color": "springgreen"},
        name=i18n.translate("target_path"),
    )

    fig = graph_objects.Figure(data=[terrain, path, start_point_scatter, destination_scatter])
    fig.update_layout(
        title=i18n.translate("terrain_and_path"),
        height=800,
        scene={
            "xaxis": {"title": "X", "dtick": 10},
            "yaxis": {"title": "Y", "dtick": 10},
            "zaxis": {"title": "Z", "dtick": 5},
            "aspectmode": "cube",
            "camera_eye": _calculate_camera_eye(elev=30, azim=240),
        },
    )
    st.plotly_chart(fig, width="stretch")


def plot_terrain_and_multipath(
    xx: np.ndarray,
    yy: np.ndarray,
    zz: np.ndarray,
    start_point: np.ndarray,
    destination: np.ndarray,
    multi_algorithm_fusion_result: MultiAlgorithmFusionResult,
) -> None:
    """Plot the terrain and multipath using Plotly.

    Args:
        xx: X coordinates of the terrain.
        yy: Y coordinates of the terrain.
        zz: Z coordinates of the terrain.
        start_point: Start point of the path.
        destination: Destination of the path.
        multi_algorithm_fusion_result: Multi-algorithm fusion result.
    """
    fig = graph_objects.Figure()

    terrain = graph_objects.Surface(x=xx, y=yy, z=zz, showscale=False, name=i18n.translate("terrain"))
    fig.add_trace(terrain)

    start_point_scatter = graph_objects.Scatter3d(
        x=[start_point[0]],
        y=[start_point[1]],
        z=[start_point[2]],
        mode="markers",
        marker={"size": 5, "color": "green"},
        name=i18n.translate("start_point"),
    )
    fig.add_trace(start_point_scatter)

    destination_scatter = graph_objects.Scatter3d(
        x=[destination[0]],
        y=[destination[1]],
        z=[destination[2]],
        mode="markers",
        marker={"size": 5, "color": "red"},
        name=i18n.translate("destination"),
    )
    fig.add_trace(destination_scatter)

    pso_path_points = multi_algorithm_fusion_result.pso_full_path_points
    pso_smooth_path_points = interpolate.smooth_path_with_cubic_spline(pso_path_points)
    pso_smooth_x, pso_smooth_y, pso_smooth_z = (
        pso_smooth_path_points[:, 0],
        pso_smooth_path_points[:, 1],
        pso_smooth_path_points[:, 2],
    )
    pso_path = graph_objects.Scatter3d(
        x=pso_smooth_x,
        y=pso_smooth_y,
        z=pso_smooth_z,
        mode="lines",
        line={"width": 6, "color": "#ff4848"},
        name=i18n.translate("pso_path"),
    )
    fig.add_trace(pso_path)

    ga_path_points = multi_algorithm_fusion_result.ga_full_path_points
    ga_smooth_path_points = interpolate.smooth_path_with_cubic_spline(ga_path_points)
    ga_smooth_x, ga_smooth_y, ga_smooth_z = (
        ga_smooth_path_points[:, 0],
        ga_smooth_path_points[:, 1],
        ga_smooth_path_points[:, 2],
    )
    ga_path = graph_objects.Scatter3d(
        x=ga_smooth_x,
        y=ga_smooth_y,
        z=ga_smooth_z,
        mode="lines",
        line={"width": 6, "color": "springgreen"},
        name=i18n.translate("ga_path"),
    )
    fig.add_trace(ga_path)

    pso_ga_hybrid_path_points = multi_algorithm_fusion_result.pso_ga_hybrid_full_path_points
    pso_ga_hybrid_smooth_path_points = interpolate.smooth_path_with_cubic_spline(pso_ga_hybrid_path_points)
    pso_ga_hybrid_smooth_x, pso_ga_hybrid_smooth_y, pso_ga_hybrid_smooth_z = (
        pso_ga_hybrid_smooth_path_points[:, 0],
        pso_ga_hybrid_smooth_path_points[:, 1],
        pso_ga_hybrid_smooth_path_points[:, 2],
    )
    pso_ga_hybrid_path = graph_objects.Scatter3d(
        x=pso_ga_hybrid_smooth_x,
        y=pso_ga_hybrid_smooth_y,
        z=pso_ga_hybrid_smooth_z,
        mode="lines",
        line={"width": 6, "color": "yellow"},
        name=i18n.translate("pso_ga_hybrid_path"),
    )
    fig.add_trace(pso_ga_hybrid_path)

    fig.update_layout(
        title=i18n.translate("terrain_and_path"),
        height=800,
        scene={
            "xaxis": {"title": "X", "dtick": 10},
            "yaxis": {"title": "Y", "dtick": 10},
            "zaxis": {"title": "Z", "dtick": 5},
            "aspectmode": "cube",
            "camera_eye": _calculate_camera_eye(elev=30, azim=240),
        },
    )
    st.plotly_chart(fig, width="stretch")


def plot_multiple_fitness_curves(multi_algorithm_fusion_result: MultiAlgorithmFusionResult) -> None:
    """Plot multiple fitness curves using Plotly.

    Args:
        multi_algorithm_fusion_result (MultiAlgorithmFusionResult): Multi-algorithm fusion result.
    """
    fig = graph_objects.Figure()

    pso_best_fitness_values = multi_algorithm_fusion_result.pso_best_fitness_values
    fig.add_trace(graph_objects.Scatter(y=pso_best_fitness_values, name="PSO", line={"color": "#ff4848"}))

    ga_best_fitness_values = multi_algorithm_fusion_result.ga_best_fitness_values
    fig.add_trace(graph_objects.Scatter(y=ga_best_fitness_values, name="GA", line={"color": "springgreen"}))

    pso_ga_hybrid_best_fitness_values = multi_algorithm_fusion_result.pso_ga_hybrid_best_fitness_values
    fig.add_trace(
        graph_objects.Scatter(y=pso_ga_hybrid_best_fitness_values, name="PSO-GA Hybrid", line={"color": "yellow"})
    )

    fig.update_layout(
        title=i18n.translate("fitness_curve"),
        xaxis_title=i18n.translate("iterations"),
        yaxis_title=i18n.translate("fitness"),
    )
    st.plotly_chart(fig, width="stretch")
