from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    stop: bool
    reason: str
    nearest_obstacle: float | None


def evaluate_scan(
    ranges: list[float] | tuple[float, ...],
    range_min: float,
    range_max: float,
    stop_distance: float,
) -> SafetyDecision:
    valid = [
        value for value in ranges
        if math.isfinite(value) and max(0.0, range_min) <= value <= range_max
    ]
    if not valid:
        return SafetyDecision(True, "no_valid_lidar_ranges", None)
    nearest = min(valid)
    if nearest <= stop_distance:
        return SafetyDecision(True, "obstacle_inside_stop_distance", nearest)
    return SafetyDecision(False, "clear", nearest)
