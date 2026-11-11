import logging
from datetime import date

import pytest

from traffic_insights.data import load_victims_csv

HEADER = "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"


def test_load_preserves_codes_unknown_locations_and_duplicate_rows(tmp_path):
    path = tmp_path / "victimas.csv"
    path.write_text(
        "\ufeff" + HEADER
        + '01/01/2024,05,ANTIOQUIA,05001,MEDELLÍN,2\n' * 2
        + "02/01/2024,15,BOYACÁ,15000,SIN ESTABLECER,1\n"
        + "03/01/2024,0,SIN ESTABLECER,0,SIN ESTABLECER,1\n",
        encoding="utf-8",
    )

    result = load_victims_csv(path)

    assert len(result.records) == 4
    assert result.records[0].event_date == date(2024, 1, 1)
    assert result.records[0].department_code == "05"
    assert result.records[0].municipality_code == "05001"
    assert result.records[0].quantity == 2
    assert result.records[2].municipality_code == "15000"
    assert result.records[3].department_code == "0"
    assert not result.rejected


def test_reports_invalid_rows_without_dropping_valid_records(tmp_path, caplog):
    path = tmp_path / "victimas.csv"
    path.write_text(
        HEADER
        + "01/01/2024,05,ANTIOQUIA,05001,MEDELLÍN,3\n"
        + "31/02/2024,05,ANTIOQUIA,05001,MEDELLÍN,1\n"
        + "01/01/2024,05,ANTIOQUIA,05001,MEDELLÍN,-1\n"
        + "01/01/2024,05,ANTIOQUIA,5001,MEDELLÍN,1\n"
        + "01/01/2024,05,ANTIOQUIA,08001,BARRANQUILLA,1\n"
        + "01/01/2024,05,ANTIOQUIA,05001,MEDELLÍN\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        result = load_victims_csv(path)

    assert len(result.records) == 1
    assert [row.line for row in result.rejected] == [3, 4, 5, 6, 7]
    assert "FECHA HECHO" in result.rejected[0].reason
    assert "CANTIDAD" in result.rejected[1].reason
    assert "COD_MUNI" in result.rejected[2].reason
    assert "COD_DEPTO" in result.rejected[3].reason
    assert "columnas" in result.rejected[4].reason
    assert "5 registros" in caplog.text


def test_missing_file_and_required_columns_raise_explicit_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_victims_csv(tmp_path / "missing.csv")

    path = tmp_path / "incomplete.csv"
    path.write_text("FECHA HECHO,CANTIDAD\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        load_victims_csv(path)


def test_rejects_all_invalid_or_malformed_csv(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text(HEADER + "no-es-fecha,05,ANTIOQUIA,05001,MEDELLÍN,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="primer rechazo en línea 2"):
        load_victims_csv(path)

    path.write_text(HEADER + '"01/01/2024,05', encoding="utf-8")
    with pytest.raises(ValueError, match="CSV inválido"):
        load_victims_csv(path)
