from __future__ import annotations

from enum import IntEnum
from typing import Any
from pydantic import BaseModel, Field
from pathlib import Path


class ItemType(IntEnum):
    POINT = 0
    POLYGON = 1
    MAP = 2


class MapParams(BaseModel):
    map_file: Path
    map_id: str
    map_montage: int
    map_section: int
    map_binning: int
    map_mag_ind: int
    map_camera: int
    map_scale_mat: tuple[float, float, float, float]
    map_width_height: tuple[int, int]


class NavItem(BaseModel):
    label: str
    color: int
    x: float
    y: float
    z: float
    type: ItemType
    regis: int
    acquire: str = Field(default="")
    note: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class NavFile(BaseModel):
    adoc_version: str
    last_saved_as: Path
    items: list[NavItem] = Field(default_factory=list)


def parse_nav(nav: str) -> NavFile:
    lines = nav.splitlines()
    obj = {}
    items: list[NavItem] = []
    while lines:
        line = lines.pop(0)
        if " = " in line:
            key, value = line.split(" = ")
            if key == "AdocVersion":
                obj["adoc_version"] = value.strip()
            elif key == "LastSavedAs":
                obj["last_saved_as"] = Path(value.strip())
        if line == "":
            continue
        if _is_item_header(line):
            label = line[8:-1]
            item = parse_item(lines, label)
            items.append(item)
    obj["items"] = items
    return NavFile(**obj)


def parse_item(lines: list[str], label: str) -> NavItem:
    obj = {"label": label}
    meta = {}
    while lines:
        line = lines.pop(0)
        if " = " in line:
            key, value = line.split(" = ")
            if key == "Color":
                obj["color"] = int(value.strip())
            elif key == "StageXYZ":
                obj["x"], obj["y"], obj["z"] = map(float, value.strip().split())
            elif key == "Type":
                obj["type"] = ItemType(int(value.strip()))
            elif key == "Regis":
                obj["regis"] = int(value.strip())
            elif key == "Acquire":
                obj["acquire"] = value.strip()
            elif key == "Note":
                obj["note"] = value
            else:
                meta[key] = value
        if line == "":
            break

    obj["metadata"] = meta
    return NavItem(**obj)


def _is_item_header(line: str) -> bool:
    return line.startswith("[Item = ") and line.endswith("]")
