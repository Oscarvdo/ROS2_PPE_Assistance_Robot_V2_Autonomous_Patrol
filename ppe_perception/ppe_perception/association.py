from __future__ import annotations

from dataclasses import dataclass

from .models import Box, Detection


@dataclass(frozen=True)
class AssociationConfig:
    helmet_upper_ratio: float = 0.38
    vest_top_ratio: float = 0.25
    vest_bottom_ratio: float = 0.78


def point_in_box(point: tuple[float, float], box: Box) -> bool:
    x, y = point
    return box.xmin <= x <= box.xmax and box.ymin <= y <= box.ymax


def person_region(person: Box, top_ratio: float, bottom_ratio: float) -> Box:
    return Box(
        person.xmin,
        person.ymin + person.height * top_ratio,
        person.xmax,
        person.ymin + person.height * bottom_ratio,
    )


def best_associated_item(
    person: Box, items: list[Detection], region: Box
) -> Detection | None:
    candidates = [item for item in items if point_in_box(item.box.center, region)]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.confidence)


def associate_ppe(
    person: Box,
    helmets: list[Detection],
    vests: list[Detection],
    config: AssociationConfig,
) -> tuple[Detection | None, Detection | None]:
    helmet_region = person_region(person, 0.0, config.helmet_upper_ratio)
    vest_region = person_region(person, config.vest_top_ratio, config.vest_bottom_ratio)
    return (
        best_associated_item(person, helmets, helmet_region),
        best_associated_item(person, vests, vest_region),
    )
