import math

import pytest

from ppe_navigation.route import load_route
from ppe_navigation.safety import evaluate_scan


def test_route_loader(tmp_path):
    route_file = tmp_path / "route.yaml"
    route_file.write_text("""waypoints:
  - name: aisle
    x: 1.25
    y: -0.5
    yaw: 1.5708
    dwell_seconds: 3
""", encoding="utf-8")
    route = load_route(route_file)
    assert route[0].name == "aisle"
    assert route[0].dwell_seconds == 3.0


def test_route_rejects_duplicate_names(tmp_path):
    route_file = tmp_path / "route.yaml"
    route_file.write_text("""waypoints:
  - {name: repeated, x: 0, y: 0}
  - {name: repeated, x: 1, y: 1}
""", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_route(route_file)


def test_safety_scan_stops_for_obstacle_and_invalid_data():
    clear = evaluate_scan([1.0, 2.0, math.inf], 0.05, 12.0, 0.4)
    assert not clear.stop
    blocked = evaluate_scan([1.0, 0.3, 2.0], 0.05, 12.0, 0.4)
    assert blocked.stop and blocked.reason == "obstacle_inside_stop_distance"
    invalid = evaluate_scan([math.nan, math.inf], 0.05, 12.0, 0.4)
    assert invalid.stop and invalid.reason == "no_valid_lidar_ranges"
