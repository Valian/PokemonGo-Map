def get_direction_string(origin, target):
    diff = target - origin
    direction = ''
    eps = 1e-4
    if abs(diff.lat().degrees) > eps:
        direction += 'N' if diff.lat().degrees >= 0 else 'S'
    if abs(diff.lng().degrees) > eps:
        direction += 'E' if diff.lng().degrees >= 0 else 'W'
    return direction


def get_distance(origin, target):
    radians_to_meters = 6366468.241830914
    return origin.get_distance(target).radians * radians_to_meters