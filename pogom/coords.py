import math

# Constants for Hex Grid
# Gap between vertical and horzonal "rows"
lat_gap_meters = 150
lng_gap_meters = 86.6

# 111111m is approx 1 degree Lat, which is close enough for this
meters_per_degree = 111111
lat_gap_degrees = float(lat_gap_meters) / meters_per_degree


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


def calculate_lng_degrees(latitude):
    degrees = math.cos(math.radians(latitude))
    return float(lng_gap_meters) / (meters_per_degree * degrees)
