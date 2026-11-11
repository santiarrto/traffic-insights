import json

import pyarrow as pa
from streamlit.testing.v1 import AppTest

from traffic_insights.visualization import select_features, style_features


def feature(code, name, field, name_field, count=None):
    return {
        "type": "Feature",
        "properties": {field: code, name_field: name, "victim_count": count},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-75, 4], [-74, 4], [-74, 5], [-75, 4]]],
        },
    }


def write_geo(path, features):
    for item in features:
        del item["properties"]["victim_count"]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


def make_data(tmp_path):
    raw = tmp_path / "raw"
    geo = tmp_path / "geo"
    raw.mkdir()
    geo.mkdir()
    csv = raw / "lesiones.csv"
    csv.write_text(
        "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"
        "01/01/2025,05,Antioquia,05001,Medellin,4\n"
        "02/01/2025,0,SIN ESTABLECER,0,SIN ESTABLECER,3\n"
        "fecha,05,Antioquia,05001,Medellin,1\n", encoding="utf-8"
    )
    write_geo(geo / "departamentos_2025.geojson", [
        feature("05", "Antioquia", "dpto_ccdgo", "dpto_cnmbr"),
        feature("08", "Atlantico", "dpto_ccdgo", "dpto_cnmbr"),
    ])
    write_geo(geo / "municipios_2025.geojson", [
        feature("05001", "Medellin", "mpio_cdpmp", "mpio_cnmbr"),
        feature("08001", "Barranquilla", "mpio_cdpmp", "mpio_cnmbr"),
    ])
    return csv


def test_display_selection_and_missing_values():
    features = [
        feature("05001", "Medellin", "mpio_cdpmp", "mpio_cnmbr", 0),
        feature("05002", "Otro", "mpio_cdpmp", "mpio_cnmbr"),
        feature("08001", "Barranquilla", "mpio_cdpmp", "mpio_cnmbr", 5),
    ]
    styled = style_features(select_features(features, "05"), "municipality")
    assert len(styled) == 2
    assert styled[0]["properties"]["map_count"] == "0"
    assert styled[1]["properties"]["map_count"] == "Sin registros"
    assert styled[0]["properties"]["map_color"] != styled[1]["properties"]["map_color"]
    assert "map_color" not in features[0]["properties"]


def test_app_both_levels_and_replaced_csv(tmp_path):
    csv = make_data(tmp_path)
    app = AppTest.from_string(
        f"from pathlib import Path\nfrom traffic_insights.app import main\nmain(Path({str(tmp_path)!r}))"
    ).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "7"
    assert any("1 registros inválidos" in warning.value for warning in app.warning)
    assert any("3 víctimas" in warning.value for warning in app.warning)

    app.radio[0].set_value("Municipios").run(timeout=30)
    assert not app.exception
    assert app.selectbox[1].value == "05"
    assert any("3 víctimas" in warning.value for warning in app.warning)
    map_data = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    features = map_data["layers"][0]["data"]["features"]
    assert [item["properties"]["mpio_cdpmp"] for item in features] == ["05001"]
    assert features[0]["properties"]["victim_count"] == 4

    csv.write_text(
        "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"
        "01/01/2025,05,Antioquia,05001,Medellin,12\n", encoding="utf-8"
    )
    app.run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "12"
    assert any("0 víctimas" in warning.value for warning in app.warning)
    map_data = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    assert map_data["layers"][0]["data"]["features"][0]["properties"]["victim_count"] == 12
    assert chart_rows(app, 0) == [{"Año": 2025, "Víctimas": 12, "Variación": "No disponible"}]

    geo = tmp_path / "geo" / "municipios_2025.geojson"
    write_geo(geo, [feature("05001", "Nombre actualizado", "mpio_cdpmp", "mpio_cnmbr")])
    app.run(timeout=30)
    assert not app.exception
    map_data = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    assert map_data["layers"][0]["data"]["features"][0]["properties"]["map_name"] == "Nombre actualizado"


def test_app_reports_missing_inputs(tmp_path):
    app = AppTest.from_string(
        f"from pathlib import Path\nfrom traffic_insights.app import main\nmain(Path({str(tmp_path)!r}))"
    ).run(timeout=30)
    assert not app.exception
    assert "No se encontró ningún CSV" in app.error[0].value


def test_app_reports_missing_geography(tmp_path):
    make_data(tmp_path)
    (tmp_path / "geo" / "departamentos_2025.geojson").unlink()
    app = AppTest.from_string(
        f"from pathlib import Path\nfrom traffic_insights.app import main\nmain(Path({str(tmp_path)!r}))"
    ).run(timeout=30)
    assert not app.exception
    assert "No se pudo preparar el mapa" in app.error[0].value


def chart_rows(app, index):
    return pa.ipc.open_stream(app.get("vega_lite_chart")[index].proto.data.data).read_all().to_pylist()


def test_statistics_render_and_update_with_ranking_and_comparison(tmp_path):
    csv = make_data(tmp_path)
    csv.write_text(
        "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"
        "01/02/2023,05,Antioquia,05001,Medellin,4\n"
        "02/01/2024,05,Antioquia,05001,Medellin,5\n"
        "03/01/2024,08,Atlantico,08001,Barranquilla,8\n"
        "03/01/2024,15,Boyaca,15000,SIN ESTABLECER,3\n",
        encoding="utf-8",
    )
    app = AppTest.from_string(
        f"from pathlib import Path\nfrom traffic_insights.app import main\nmain(Path({str(tmp_path)!r}))"
    ).run(timeout=30)
    assert not app.exception
    assert len(app.get("vega_lite_chart")) == 5
    assert any("no cubre todo el año calendario en: 2023, 2024" in w.value for w in app.warning)
    assert chart_rows(app, 0) == [
        {"Año": 2023, "Víctimas": 4, "Variación": "No disponible"},
        {"Año": 2024, "Víctimas": 16, "Variación": "+300.0 %"},
    ]
    assert chart_rows(app, 1) == [
        {"Periodo": "Enero", "Víctimas": 16}, {"Periodo": "Febrero", "Víctimas": 4},
    ]

    app.radio[1].set_value("Municipios").run(timeout=30)
    assert not app.exception
    ranking = chart_rows(app, 3)
    assert any(row["Zona"] == "SIN ESTABLECER (15000)" and row["Proporción"] == "15.00 %" for row in ranking)

    app.multiselect[0].set_value(["08"]).run(timeout=30)
    assert not app.exception
    assert chart_rows(app, 4) == [{"Año": 2024, "Departamento": "Atlantico (08)", "Víctimas": 8}]
    app.multiselect[0].set_value([]).run(timeout=30)
    assert not app.exception
    assert any("Selecciona al menos un departamento" in item.value for item in app.info)


def test_statistics_with_zero_total_do_not_invent_percentages(tmp_path):
    csv = make_data(tmp_path)
    csv.write_text(
        "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"
        "01/01/2025,05,Antioquia,05001,Medellin,0\n",
        encoding="utf-8",
    )
    app = AppTest.from_string(
        f"from pathlib import Path\nfrom traffic_insights.app import main\nmain(Path({str(tmp_path)!r}))"
    ).run(timeout=30)
    assert not app.exception
    assert chart_rows(app, 3) == [
        {"Zona": "Antioquia (05)", "Víctimas": 0, "Proporción": "No disponible"}
    ]
