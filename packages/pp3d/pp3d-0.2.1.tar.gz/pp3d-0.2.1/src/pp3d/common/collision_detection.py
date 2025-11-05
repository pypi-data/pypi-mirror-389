import numpy as np
from scipy.interpolate import RegularGridInterpolator


def check_vertical_collision_batch(
    xx: np.ndarray, yy: np.ndarray, zz: np.ndarray, points: np.ndarray, min_safe_distance: float = 1.0
) -> np.ndarray:
    """
    Check if the given points collide with the terrain vertically.

    Args:
        xx (np.ndarray): The x coordinates of the terrain height map.
        yy (np.ndarray): The y coordinates of the terrain height map.
        zz (np.ndarray): The z coordinates of the terrain height map.
        points (np.ndarray): The points to check for collision. Shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        min_safe_distance (float, optional): The minimum safe distance to the terrain vertically. Defaults to 1.0.

    Returns:
        np.ndarray: True if the given points collide with the terrain vertically, False otherwise.
                    Shape: (N,), i.e. [True, False, True, ...]
    """
    terrain_x = xx[0, :]
    terrain_y = yy[:, 0]

    # NOTE: The `points` is (terrain_y, terrain_x) here, NOT (terrain_x, terrain_y)
    interpolator = RegularGridInterpolator(points=(terrain_y, terrain_x), values=zz, bounds_error=False, fill_value=0)

    points_x = points[:, 0]
    points_y = points[:, 1]
    points_z = points[:, 2]

    x_min, x_max = xx.min(), xx.max()
    y_min, y_max = yy.min(), yy.max()
    points_x_clipped = np.clip(points_x, x_min, x_max)
    points_y_clipped = np.clip(points_y, y_min, y_max)

    points_to_interpolate = np.column_stack((points_y_clipped, points_x_clipped))

    terrain_z = interpolator(points_to_interpolate)
    safe_height = terrain_z + min_safe_distance

    collisions = points_z < safe_height

    return collisions


def check_horizontal_collision_batch(
    points: np.ndarray, peaks: list[tuple[float, float, float, float]], min_safe_distance: float = 1.0
) -> np.ndarray:
    """
    Check if the given points collide with the terrain horizontally.

    Args:
        points (np.ndarray): The points to check for collision. Shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        peaks (list[tuple[float, float, float, float]]):
            The list of peaks. Each peak is a tuple of (center_x, center_y, amplitude, radius).
        min_safe_distance (float, optional): The minimum safe distance to the terrain horizontally. Defaults to 1.0.

    Returns:
        np.ndarray: True if the given points collide with the terrain horizontally, False otherwise.
                    Shape: (N,), i.e. [True, False, True, ...]
    """
    points_x = points[:, 0]
    points_y = points[:, 1]
    points_z = points[:, 2]

    peaks_array = np.array(peaks)
    peaks_center_x = peaks_array[:, 0]
    peaks_center_y = peaks_array[:, 1]
    peaks_amplitude = peaks_array[:, 2]
    peaks_radius = peaks_array[:, 3]

    # Calculate the log expression for each peak and point
    # peaks_amplitude shape: (M,) to (1, M)
    # points_z shape: (N,) to (N, 1)
    # log_expression shape: (N, M)
    log_expression = 10 * peaks_amplitude[None, :] / points_z[:, None]

    # valid_mask shape: (N, M)
    valid_mask = (
        (points_z[:, None] > 0) & (peaks_amplitude[None, :] > 0) & (peaks_radius[None, :] > 0) & (log_expression > 0)
    )

    # log_value shape: (N, M)
    log_value = np.zeros_like(log_expression)
    log_value[valid_mask] = np.log(log_expression[valid_mask])

    # Check if log_value is non-negative
    valid_mask &= log_value >= 0

    # Calculate the radius of the section of the peaks
    peak_section_radius = np.zeros_like(log_value)
    peaks_radius_broadcasted = np.broadcast_to(peaks_radius[None, :], log_value.shape)
    peak_section_radius[valid_mask] = peaks_radius_broadcasted[valid_mask] * np.sqrt(2 * log_value[valid_mask])

    # Calculate the distance from each point to the center of each peak
    # Shape: (N, 1) - (1, M) = (N, M)
    dx = points_x[:, None] - peaks_center_x[None, :]
    dy = points_y[:, None] - peaks_center_y[None, :]
    distance_to_peaks_center = np.sqrt(dx**2 + dy**2)

    collision_matrix = distance_to_peaks_center < (peak_section_radius + min_safe_distance)

    collisions = np.any(collision_matrix, axis=1)

    return collisions
