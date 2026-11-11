import io
import json

import pytest

from traffic_insights import download_geography


def response(data):
    class Response(io.BytesIO):
        headers = {}

    return Response(json.dumps(data).encode("utf-8"))


def feature(code):
    return {
        "type": "Feature",
        "properties": {"mpio_cdpmp": code},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-75, 4], [-74, 4], [-74, 5], [-75, 4]]],
        },
    }


def test_paged_download_preserves_codes_and_replaces_only_after_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(download_geography, "PAGE_SIZE", 2)

    def fake_urlopen(request, timeout):
        if "returnCountOnly" in request.full_url:
            return response({"count": 3})
        codes = ["05001", "05002"] if "resultOffset=0" in request.full_url else ["08001"]
        return response({
            "type": "FeatureCollection",
            "features": [feature(code) for code in codes],
        })

    monkeypatch.setattr(download_geography, "urlopen", fake_urlopen)
    output = tmp_path / "municipios.geojson"
    output.write_text("original", encoding="utf-8")
    assert download_geography.download_municipalities(output) == 3
    features = json.loads(output.read_text(encoding="utf-8"))["features"]
    assert [feature["properties"]["mpio_cdpmp"] for feature in features] == ["05001", "05002", "08001"]


def test_incomplete_or_duplicate_page_does_not_replace_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(download_geography, "PAGE_SIZE", 2)

    def fake_urlopen(request, timeout):
        if "returnCountOnly" in request.full_url:
            return response({"count": 2})
        return response({
            "features": [
                feature("05001"),
                feature("05001"),
            ]
        })

    monkeypatch.setattr(download_geography, "urlopen", fake_urlopen)
    output = tmp_path / "municipios.geojson"
    output.write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        download_geography.download_municipalities(output)
    assert output.read_text(encoding="utf-8") == "original"


def test_incomplete_page_does_not_replace_destination(tmp_path, monkeypatch):
    def fake_urlopen(request, timeout):
        if "returnCountOnly" in request.full_url:
            return response({"count": 2})
        return response({"features": [feature("05001")]})

    monkeypatch.setattr(download_geography, "urlopen", fake_urlopen)
    output = tmp_path / "municipios.geojson"
    output.write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="Página incompleta"):
        download_geography.download_municipalities(output)
    assert output.read_text(encoding="utf-8") == "original"


def test_invalid_geometry_does_not_replace_destination(tmp_path, monkeypatch):
    def fake_urlopen(request, timeout):
        if "returnCountOnly" in request.full_url:
            return response({"count": 1})
        item = feature("05001")
        item["geometry"] = None
        return response({"features": [item]})

    monkeypatch.setattr(download_geography, "urlopen", fake_urlopen)
    output = tmp_path / "municipios.geojson"
    output.write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="Geometría ausente"):
        download_geography.download_municipalities(output)
    assert output.read_text(encoding="utf-8") == "original"
