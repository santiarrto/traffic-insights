"""Descarga manual y paginada de la capa municipal del DANE."""

import argparse
import gzip
import json
import logging
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import ijson

from traffic_insights.geography import validate_geometry

logger = logging.getLogger(__name__)
QUERY_URL = (
    "https://services.arcgis.com/ioNRSZMYYlx0PUaB/arcgis/rest/services/"
    "MGN2025_MPIO_GRAFICO/FeatureServer/0/query"
)
PAGE_SIZE = 100


@contextmanager
def _response(params: dict[str, str | int]):
    request = Request(f"{QUERY_URL}?{urlencode(params)}", headers={"Accept-Encoding": "gzip"})
    for attempt in range(3):
        try:
            response = urlopen(request, timeout=120)
            break
        except URLError:
            if attempt == 2:
                raise
            logger.warning("No se pudo conectar al DANE; reintentando (%d/2)", attempt + 1)
            time.sleep(attempt + 1)
    with response:
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            with gzip.GzipFile(fileobj=response) as decoded:
                yield decoded
        else:
            yield response


def _count() -> int:
    with _response({"where": "1=1", "returnCountOnly": "true", "f": "json"}) as response:
        result = json.load(response)
    count = result.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError(f"El servicio no devolvió un conteo válido: {result}")
    return count


def download_municipalities(destination: str | Path) -> int:
    """Descarga todas las páginas y reemplaza el destino solo al comprobarlas."""
    output = Path(destination)
    count = _count()
    seen: set[str] = set()
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as file:
            temporary_path = Path(file.name)
            file.write('{"type":"FeatureCollection","features":[')
            first = True
            for offset in range(0, count, PAGE_SIZE):
                params = {
                    "where": "1=1",
                    "outFields": "mpio_cdpmp,mpio_cnmbr,dpto_ccdgo",
                    "outSR": 4326,
                    "orderByFields": "mpio_cdpmp",
                    "resultOffset": offset,
                    "resultRecordCount": PAGE_SIZE,
                    "f": "geojson",
                }
                page_count = 0
                with _response(params) as response:
                    for feature in ijson.items(response, "features.item", use_float=True):
                        properties = feature.get("properties") if isinstance(feature, dict) else None
                        code = properties.get("mpio_cdpmp") if isinstance(properties, dict) else None
                        if not isinstance(code, str) or not re.fullmatch(r"[0-9]{5}", code):
                            raise ValueError(f"Código municipal inválido: {code!r}")
                        if code in seen:
                            raise ValueError(f"Código municipal duplicado: {code}")
                        if feature.get("type") != "Feature":
                            raise ValueError(f"Elemento GeoJSON inválido para el código {code}")
                        validate_geometry(feature.get("geometry"), code)
                        seen.add(code)
                        if not first:
                            file.write(",")
                        json.dump(feature, file, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                        first = False
                        page_count += 1
                expected = min(PAGE_SIZE, count - offset)
                if page_count != expected:
                    raise ValueError(
                        f"Página incompleta desde {offset}: se esperaban {expected} geometrías "
                        f"y se recibieron {page_count}"
                    )
                logger.info("Descargadas %d de %d geometrías", len(seen), count)
            file.write("]}")
        if _count() != count:
            raise ValueError("El conteo de la capa cambió durante la descarga")
        os.replace(temporary_path, output)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return len(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description="Descargar la capa municipal MGN 2025 del DANE.")
    parser.add_argument("destino", type=Path, help="Ruta del archivo GeoJSON de salida")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        count = download_municipalities(args.destino)
    except (OSError, ValueError, ijson.JSONError) as exc:
        parser.exit(1, f"No se pudo descargar la capa municipal: {exc}\n")
    print(f"Descarga completa: {count} geometrías en {args.destino}")


if __name__ == "__main__":
    main()
