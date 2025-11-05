import random

def generate_bezier_path(start_point, end_point, steps=20):
    """
    Generates points for a quadratic Bezier curve.
    :param start_point: dict with 'x' and 'y' keys
    :param end_point: dict with 'x' and 'y' keys
    :param steps: number of points to generate
    :return: list of point dicts
    """
    path = []

    mid_point = {
        "x": (start_point["x"] + end_point["x"]) / 2,
        "y": (start_point["y"] + end_point["y"]) / 2,
    }

    control_point = {
        "x": mid_point["x"] + (random.random() - 0.5) * 100,
        "y": mid_point["y"] + (random.random() - 0.5) * 100,
    }

    for i in range(steps + 1):
        t = i / steps
        x = round((1 - t)**2 * start_point["x"] + 2 * (1 - t) * t * control_point["x"] + t**2 * end_point["x"])
        y = round((1 - t)**2 * start_point["y"] + 2 * (1 - t) * t * control_point["y"] + t**2 * end_point["y"])
        path.append({"x": x, "y": y})

    return path