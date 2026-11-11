"""Preparación de datos para visualizar mapas sin modificar las fuentes."""

import json
import math
import tempfile
from pathlib import Path
from typing import Sequence

from shapely.geometry import shape

from traffic_insights.analysis import GeographicTotal
from traffic_insights.geography import GeographicLevel, prepare_map

DISPLAY_TOLERANCE = 0.001


def display_features(
    source: Path, level: GeographicLevel, totals: Sequence[GeographicTotal]
) -> tuple[list[dict], tuple[GeographicTotal, ...]]:
    with tempfile.TemporaryDirectory(prefix="traffic-insights-") as directory:
        output = Path(directory) / "map.geojson"
        result = prepare_map(source, output, level, totals, simplify_tolerance=DISPLAY_TOLERANCE)
        with output.open(encoding="utf-8") as file:
            features = json.load(file)["features"]
    return features, result.unmatched


def select_features(features: list[dict], department: str | None) -> list[dict]:
    if department is None:
        return features
    return [
        feature for feature in features
        if feature["properties"]["mpio_cdpmp"].startswith(department)
    ]


def style_features(features: list[dict], level: GeographicLevel) -> list[dict]:
    name_field = "dpto_cnmbr" if level == "department" else "mpio_cnmbr"
    code_field = "dpto_ccdgo" if level == "department" else "mpio_cdpmp"
    maximum = max((f["properties"]["victim_count"] or 0 for f in features), default=0)
    styled = []
    for feature in features:
        properties = feature["properties"].copy()
        count = properties["victim_count"]
        if count is None:
            color = [160, 160, 160, 180]
            label = "Sin registros"
        else:
            intensity = math.log1p(count) / math.log1p(maximum) if maximum else 0
            color = [255, round(225 - 180 * intensity), round(130 - 100 * intensity), 200]
            label = f"{count:,}".replace(",", ".")
        properties["map_color"] = color
        properties["map_name"] = properties.get(name_field) or properties[code_field]
        properties["map_count"] = label
        styled.append({**feature, "properties": properties})
    return styled


def map_view(features: list[dict]) -> tuple[float, float, float]:
    if not features:
        raise ValueError("No hay geometrías para mostrar en el mapa")
    bounds = [shape(feature["geometry"]).bounds for feature in features]
    west = min(item[0] for item in bounds)
    south = min(item[1] for item in bounds)
    east = max(item[2] for item in bounds)
    north = max(item[3] for item in bounds)
    span = max(east - west, (north - south) * 1.5, 0.1)
    zoom = max(3.0, min(9.0, math.log2(360 / span) - 1.5))
    return (west + east) / 2, (south + north) / 2, zoom
