import numpy as np
from scipy.interpolate import CubicSpline


def smooth_path_with_cubic_spline(path_points: np.ndarray, num_interpolated_points: int = 100) -> np.ndarray:
    """Smooth the path with cubic spline interpolation.

    Args:
        path_points: Path points to be smoothed, shape: (n, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        num_interpolated_points: Number of interpolated points.

    Returns:
        Smoothed path points, shape: (num_interpolated_points, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
    """
    t = np.linspace(start=0, stop=1, num=len(path_points))

    x = path_points[:, 0]
    y = path_points[:, 1]
    z = path_points[:, 2]

    spline_x = CubicSpline(t, x)
    spline_y = CubicSpline(t, y)
    spline_z = CubicSpline(t, z)

    t_new = np.linspace(start=0, stop=1, num=num_interpolated_points)

    smooth_x = spline_x(t_new)
    smooth_y = spline_y(t_new)
    smooth_z = spline_z(t_new)

    smooth_path_points = np.column_stack((smooth_x, smooth_y, smooth_z))

    return smooth_path_points
