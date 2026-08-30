from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Waypoint:
    name: str
    x: float
    y: float
    yaw: float
    dwell_seconds: float = 0.0


def load_route(path: str | Path) -> list[Waypoint]:
    route_path = Path(path)
    payload = yaml.safe_load(route_path.read_text(encoding="utf-8")) or {}
    raw_waypoints = payload.get("waypoints")
    if not isinstance(raw_waypoints, list) or not raw_waypoints:
        raise ValueError("Route YAML must contain a non-empty 'waypoints' list")
    route: list[Waypoint] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_waypoints):
        if not isinstance(raw, dict):
            raise ValueError(f"Waypoint {index} must be an object")
        name = str(raw.get("name", f"waypoint_{index + 1}"))
        if name in names:
            raise ValueError(f"Duplicate waypoint name: {name}")
        names.add(name)
        waypoint = Waypoint(
            name=name,
            x=float(raw["x"]),
            y=float(raw["y"]),
            yaw=float(raw.get("yaw", 0.0)),
            dwell_seconds=max(0.0, float(raw.get("dwell_seconds", 0.0))),
        )
        if not all(math.isfinite(value) for value in (waypoint.x, waypoint.y, waypoint.yaw)):
            raise ValueError(f"Waypoint {name} contains non-finite coordinates")
        route.append(waypoint)
    return route
