# The code template for terrain generation function
TERRAIN_GENERATION_CODE_TEMPLATE = """
def generate_terrain(xx: np.ndarray, yy: np.ndarray) -> np.ndarray:
    peaks=[
        # (center_x, center_y, amplitude, radius)
        (20, 20, 5, 8),
        (20, 70, 5, 8),
        (60, 20, 5, 8),
        (60, 70, 5, 8)
    ]
    
    zz = np.zeros_like(xx)
    
    for peak in peaks:
        center_x, center_y, amplitude, radius = peak
        zz += 10 * amplitude * np.exp(-((xx - center_x) ** 2 + (yy - center_y) ** 2) / (2 * radius ** 2))
    
    zz += 0.2 * np.sin(0.5 * np.sqrt(xx**2 + yy**2)) + 0.1 * np.random.normal(size=xx.shape)
    
    zz = gaussian_filter(zz, sigma=3)
    
    zz = np.clip(zz, 0, None)
    
    return zz
""".strip()

# The code template for fitness function
FITNESS_FUNCTION_CODE_TEMPLATE = """
def fitness_function(path_points: np.ndarray) -> float:
    reshaped_path_points = path_points.reshape(-1, 3)
    full_path_points = np.vstack([start_point, reshaped_path_points, destination])
    full_path_points = interpolate.smooth_path_with_cubic_spline(full_path_points)
    
    peaks=[
        # (center_x, center_y, amplitude, radius)
        (20, 20, 5, 8),
        (20, 70, 5, 8),
        (60, 20, 5, 8),
        (60, 70, 5, 8)
    ]
    
    # Calculate the horizontal collision cost
    min_horizontal_safe_distance = 1
    collision_cost = np.sum(
        collision_detection.check_horizontal_collision_batch(full_path_points, peaks, min_horizontal_safe_distance)
    )
    
    # Calculate the path length cost in XY plane
    path_diff = np.diff(full_path_points, axis=0)
    horizontal_diff = path_diff[:, :2] # only consider XY plane
    path_length_cost = np.sum(np.sqrt(np.sum(horizontal_diff**2, axis=1)))
    
    # Calculate the path height cost
    height_diff = path_diff[:, 2] # only consider Z axis
    path_height_cost = np.sum(np.abs(height_diff))
    
    # Calculate the minimum safe height cost (also understand as the vertical collision cost)
    min_vertical_safe_distance = 1
    min_safe_height_cost = np.sum(
        collision_detection.check_vertical_collision_batch(xx, yy, zz, full_path_points, min_vertical_safe_distance)
    )
    
    # Calculate the maximum safe height from the ground surface cost
    max_safe_height = 20
    max_safe_height_cost = np.sum(full_path_points[:, 2] > max_safe_height)
    
    # Calculate the slope angle cost
    max_safe_slope_angle = 45
    slope_angle_cost = np.sum(
        flight_angle_calculator.calculate_slope_angles_batch(full_path_points[:-1], full_path_points[1:])
        > max_safe_slope_angle
    )
    
    # Calculate the horizontal turn angle cost
    max_safe_turn_angle = 45
    turn_angle_cost = np.sum(
        flight_angle_calculator.calculate_horizontal_turn_angles_batch(
            full_path_points[:-2], full_path_points[1:-1], full_path_points[2:]
        )
        > max_safe_turn_angle
    )
    
    collision_cost_weight = 1e4
    path_length_cost_weight = 1
    path_height_cost_weight = 1
    min_safe_height_cost_weight = 1e4
    max_safe_height_cost_weight = 1
    slope_angle_cost_weight = 1
    turn_angle_cost_weight = 1
    
    return (
        collision_cost_weight * collision_cost
        + path_length_cost_weight * path_length_cost
        + path_height_cost_weight * path_height_cost
        + min_safe_height_cost_weight * min_safe_height_cost
        + max_safe_height_cost_weight * max_safe_height_cost
        + slope_angle_cost_weight * slope_angle_cost
        + turn_angle_cost_weight * turn_angle_cost
    )
""".strip()
