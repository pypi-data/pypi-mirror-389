import numpy as np


def calculate_slope_angles_batch(points1: np.ndarray, points2: np.ndarray) -> np.ndarray:
    """Calculate the slope angles between two points.

    Args:
        points1: First points, shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        points2: Second points, shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]

    Returns:
        Slope angles (0°-90°) between the two points in degrees.
    """
    dx = points2[:, 0] - points1[:, 0]
    dy = points2[:, 1] - points1[:, 1]
    dz = points2[:, 2] - points1[:, 2]
    horizontal_distances = np.sqrt(dx**2 + dy**2)
    slopes = np.abs(dz) / horizontal_distances
    slopes[horizontal_distances == 0] = np.inf
    slope_angles_rad = np.arctan(slopes)
    slope_angles_deg = np.degrees(slope_angles_rad)
    return slope_angles_deg


def calculate_horizontal_turn_angles_batch(points1: np.ndarray, points2: np.ndarray, points3: np.ndarray) -> np.ndarray:
    """Calculate the horizontal turn angles between three points.

    Args:
        points1: First points, shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        points2: Second points, shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]
        points3: Third points, shape: (N, 3), i.e. [[x1, y1, z1], [x2, y2, z2], ...]

    Returns:
        Horizontal turn angles (0°-180°) between the three points in degrees.
    """
    p1p2 = points2 - points1
    p2p3 = points3 - points2

    dot_products = np.sum(p1p2 * p2p3, axis=1)

    norms_p1p2 = np.linalg.norm(p1p2, axis=1)
    norms_p2p3 = np.linalg.norm(p2p3, axis=1)

    cos_angles = dot_products / (norms_p1p2 * norms_p2p3)
    cos_angles = np.clip(cos_angles, -1, 1)
    angles_rad = np.arccos(cos_angles)
    angles_deg = np.degrees(angles_rad)
    return angles_deg
