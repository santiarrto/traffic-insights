"""Preparación incremental de geometrías e indicadores para el mapa."""

import json
import logging
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

import ijson
from ijson.common import ObjectBuilder
from shapely.geometry import mapping, shape

from traffic_insights.analysis import GeographicTotal

logger = logging.getLogger(__name__)

GeographicLevel = Literal["department", "municipality"]


@dataclass(frozen=True, slots=True)
class MapPreparation:
    output_path: Path
    feature_count: int
    matched_quantity: int
    unmatched: tuple[GeographicTotal, ...]

    @property
    def unmatched_quantity(self) -> int:
        return sum(item.quantity for item in self.unmatched)


def validate_geometry(geometry: object, code: str) -> None:
    """Valida la estructura y los rangos de un polígono GeoJSON."""
    if not isinstance(geometry, dict):
        raise ValueError(f"Geometría ausente para el código {code}")
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type not in ("Polygon", "MultiPolygon") or not isinstance(coordinates, list):
        raise ValueError(f"Geometría inválida para el código {code}")

    polygons = [coordinates] if geometry_type == "Polygon" else coordinates
    if not polygons:
        raise ValueError(f"Geometría vacía para el código {code}")
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise ValueError(f"Polígono vacío para el código {code}")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ValueError(f"Anillo inválido para el código {code}")
            for position in ring:
                if not isinstance(position, list) or len(position) < 2:
                    raise ValueError(f"Coordenada inválida para el código {code}")
                longitude, latitude = position[:2]
                if (
                    isinstance(longitude, bool)
                    or isinstance(latitude, bool)
                    or not isinstance(longitude, (int, float))
                    or not isinstance(latitude, (int, float))
                    or not math.isfinite(longitude)
                    or not math.isfinite(latitude)
                    or not -180 <= longitude <= 180
                    or not -90 <= latitude <= 90
                ):
                    raise ValueError(f"Coordenada fuera de rango para el código {code}")
            if ring[0][:2] != ring[-1][:2]:
                raise ValueError(f"Anillo sin cerrar para el código {code}")


def prepare_map(
    source_path: str | Path,
    output_path: str | Path,
    level: GeographicLevel,
    totals: Sequence[GeographicTotal],
    *,
    simplify_tolerance: float | None = None,
) -> MapPreparation:
    """Escribe un GeoJSON enriquecido y devuelve los códigos sin geometría.

    La simplificación opcional afecta únicamente al archivo de salida.
    """
    if level not in ("department", "municipality"):
        raise ValueError(f"Nivel geográfico no admitido: {level}")
    if simplify_tolerance is not None and (
        not math.isfinite(simplify_tolerance) or simplify_tolerance <= 0
    ):
        raise ValueError("La tolerancia de simplificación debe ser positiva y finita")
    source = Path(source_path)
    output = Path(output_path)
    if source.resolve() == output.resolve() or (
        source.exists() and output.exists() and os.path.samefile(source, output)
    ):
        raise ValueError("El archivo de salida no puede ser el archivo de origen")

    quantities: dict[str, int] = {}
    for item in totals:
        if item.code in quantities:
            raise ValueError(f"Código agregado duplicado: {item.code}")
        if item.quantity < 0:
            raise ValueError(f"Cantidad negativa para el código {item.code}")
        quantities[item.code] = item.quantity
    if not quantities:
        raise ValueError("No hay agregados para preparar el mapa")

    field, pattern = (
        ("dpto_ccdgo", r"[0-9]{2}")
        if level == "department"
        else ("mpio_cdpmp", r"[0-9]{5}")
    )
    seen: set[str] = set()
    matched: set[str] = set()
    collection_type = None
    features_found = False
    builder = None
    temporary_path = None
    try:
        with source.open("rb") as input_file, tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as output_file:
            temporary_path = Path(output_file.name)
            output_file.write('{"type":"FeatureCollection","features":[')
            first = True
            for prefix, event, value in ijson.parse(input_file, use_float=True):
                if prefix == "" and event not in ("start_map", "end_map", "map_key"):
                    raise ValueError("El GeoJSON debe ser un objeto")
                if prefix == "type" and event == "string":
                    collection_type = value
                if prefix in ("exceededTransferLimit", "properties.exceededTransferLimit") and value is True:
                    raise ValueError("La capa geográfica está incompleta")
                if prefix == "features" and event == "start_array":
                    if features_found:
                        raise ValueError("El GeoJSON contiene varias listas de geometrías")
                    features_found = True
                if prefix == "features.item" and builder is None:
                    if event != "start_map":
                        raise ValueError("El GeoJSON contiene un elemento inválido")
                    builder = ObjectBuilder()
                if builder is None:
                    continue
                builder.event(event, value)
                if prefix != "features.item" or event != "end_map":
                    continue
                feature = builder.value
                builder = None
                if feature.get("type") != "Feature" or not isinstance(feature.get("properties"), dict):
                    raise ValueError("El GeoJSON contiene una geometría sin propiedades válidas")
                properties = feature["properties"]
                code = properties.get(field)
                if not isinstance(code, str) or not re.fullmatch(pattern, code):
                    raise ValueError(f"Código geográfico inválido en {field}: {code!r}")
                if code in seen:
                    raise ValueError(f"Código geográfico duplicado: {code}")
                if "victim_count" in properties:
                    raise ValueError("La geometría ya contiene la propiedad victim_count")
                validate_geometry(feature.get("geometry"), code)
                if simplify_tolerance is not None:
                    simplified = shape(feature["geometry"]).simplify(
                        simplify_tolerance, preserve_topology=True
                    )
                    if simplified.is_empty:
                        raise ValueError(f"La simplificación produjo una geometría vacía: {code}")
                    feature["geometry"] = mapping(simplified)
                seen.add(code)
                if code in quantities:
                    matched.add(code)
                properties["victim_count"] = quantities.get(code)
                if not first:
                    output_file.write(",")
                json.dump(feature, output_file, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                first = False

            if collection_type != "FeatureCollection" or not features_found or not seen:
                raise ValueError("El archivo no contiene una colección GeoJSON válida con geometrías")
            output_file.write("]}")
        temporary_path.replace(output)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    unmatched = tuple(item for item in totals if item.code not in matched)
    if unmatched:
        logger.warning(
            "%s: %d códigos sin geometría; cantidad no representada: %d",
            level,
            len(unmatched),
            sum(item.quantity for item in unmatched),
        )
    return MapPreparation(
        output_path=output,
        feature_count=len(seen),
        matched_quantity=sum(quantities[code] for code in matched),
        unmatched=unmatched,
    )
