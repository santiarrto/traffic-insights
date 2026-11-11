import json
import logging

import ijson
import pytest

from traffic_insights.analysis import GeographicTotal
from traffic_insights.geography import prepare_map


def feature(code, field="mpio_cdpmp"):
    return {
        "type": "Feature",
        "properties": {field: code},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-75, 4], [-74, 4], [-74, 5], [-75, 4]]],
        },
    }


def write_collection(path, features, **extra):
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features, **extra}),
        encoding="utf-8",
    )


def test_joins_codes_preserves_unknown_and_does_not_invent_zero(tmp_path, caplog):
    source = tmp_path / "source.geojson"
    output = tmp_path / "map.geojson"
    write_collection(source, [feature("05001"), feature("05002"), feature("05003")])
    original = source.read_bytes()
    totals = [
        GeographicTotal("05001", 4),
        GeographicTotal("05002", 0),
        GeographicTotal("15000", 5),
        GeographicTotal("0", 3),
    ]

    with caplog.at_level(logging.WARNING):
        result = prepare_map(source, output, "municipality", totals)

    features = json.loads(output.read_text(encoding="utf-8"))["features"]
    assert [item["properties"]["victim_count"] for item in features] == [4, 0, None]
    assert result.feature_count == 3
    assert result.matched_quantity == 4
    assert result.unmatched == (GeographicTotal("15000", 5), GeographicTotal("0", 3))
    assert result.unmatched_quantity == 8
    assert "cantidad no representada: 8" in caplog.text
    assert source.read_bytes() == original


def test_department_join_preserves_leading_zero(tmp_path):
    source = tmp_path / "source.geojson"
    output = tmp_path / "map.geojson"
    write_collection(source, [feature("05", "dpto_ccdgo")])

    result = prepare_map(source, output, "department", [GeographicTotal("05", 2)])

    assert result.matched_quantity == 2
    assert not result.unmatched
    assert json.loads(output.read_text(encoding="utf-8"))["features"][0]["properties"] == {
        "dpto_ccdgo": "05",
        "victim_count": 2,
    }


@pytest.mark.parametrize(
    ("features", "extra", "message"),
    [
        ([feature("05001"), feature("05001")], {}, "duplicado"),
        ([feature("5001")], {}, "inválido"),
        ([{**feature("05001"), "geometry": None}], {}, "ausente"),
        ([{
            **feature("05001"),
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [2, 2]]]},
        }], {}, "sin cerrar"),
        ([feature("05001")], {"exceededTransferLimit": True}, "incompleta"),
        ([], {}, "colección GeoJSON válida"),
    ],
)
def test_invalid_layers_fail_without_overwriting_output(tmp_path, features, extra, message):
    source = tmp_path / "source.geojson"
    output = tmp_path / "map.geojson"
    write_collection(source, features, **extra)
    output.write_text("existing output", encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        prepare_map(source, output, "municipality", [GeographicTotal("05001", 1)])

    assert output.read_text(encoding="utf-8") == "existing output"


def test_rejects_source_as_destination_and_duplicate_aggregates(tmp_path):
    source = tmp_path / "source.geojson"
    write_collection(source, [feature("05001")])
    with pytest.raises(ValueError, match="salida"):
        prepare_map(source, source, "municipality", [GeographicTotal("05001", 1)])
    with pytest.raises(ValueError, match="agregado duplicado"):
        prepare_map(
            source, tmp_path / "out.geojson", "municipality",
            [GeographicTotal("05001", 1), GeographicTotal("05001", 2)],
        )


def test_truncated_geojson_keeps_previous_output(tmp_path):
    source = tmp_path / "source.geojson"
    output = tmp_path / "map.geojson"
    source.write_text('{"type":"FeatureCollection","features":[', encoding="utf-8")
    output.write_text("existing output", encoding="utf-8")

    with pytest.raises(ijson.JSONError):
        prepare_map(source, output, "municipality", [GeographicTotal("05001", 1)])

    assert output.read_text(encoding="utf-8") == "existing output"


def test_simplification_is_optional_and_preserves_source_and_counts(tmp_path):
    source = tmp_path / "source.geojson"
    output = tmp_path / "map.geojson"
    item = feature("05001")
    item["geometry"]["coordinates"] = [
        [[0, 0], [0.5, 0.00001], [1, 0], [1, 1], [0, 0]]
    ]
    write_collection(source, [item])
    original = source.read_bytes()

    prepare_map(source, output, "municipality", [GeographicTotal("05001", 2)],
                simplify_tolerance=0.001)
    simplified = json.loads(output.read_text(encoding="utf-8"))["features"][0]
    assert len(simplified["geometry"]["coordinates"][0]) == 4
    assert simplified["properties"]["victim_count"] == 2
    assert source.read_bytes() == original

    with pytest.raises(ValueError, match="tolerancia"):
        prepare_map(source, output, "municipality", [GeographicTotal("05001", 2)],
                    simplify_tolerance=float("nan"))
