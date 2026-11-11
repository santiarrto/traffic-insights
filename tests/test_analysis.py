from datetime import date

import pytest

from traffic_insights.analysis import (
    GeographicName,
    GeographicTotal,
    PeriodTotal,
    annual_changes,
    calculate_indicators,
    rank_regions,
)
from traffic_insights.data import LoadResult, load_victims_csv


def test_indicators_preserve_duplicates_unknown_locations_and_rejections(tmp_path):
    path = tmp_path / "victimas.csv"
    path.write_text(
        "FECHA HECHO,COD_DEPTO,DEPARTAMENTO,COD_MUNI,MUNICIPIO,CANTIDAD\n"
        + "01/01/2024,05,ANTIOQUIA,05001,MEDELLÍN,2\n" * 2
        + "01/03/2024,15,BOYACÁ,15000,SIN ESTABLECER,5\n"
        + "01/02/2023,0,SIN ESTABLECER,0,SIN ESTABLECER,3\n"
        + "01/02/2024,99,OTRO,99999,DESCONOCIDO,7\n"
        + "fecha inválida,05,ANTIOQUIA,05001,MEDELLÍN,9\n",
        encoding="utf-8",
    )

    indicators = calculate_indicators(load_victims_csv(path))

    assert indicators.total == 19
    assert (indicators.start_date, indicators.end_date) == (date(2023, 2, 1), date(2024, 3, 1))
    assert indicators.valid_records == 5
    assert [row.line for row in indicators.rejected] == [7]
    assert {item.code: item.quantity for item in indicators.departments} == {
        "0": 3, "05": 4, "15": 5, "99": 7,
    }
    assert {item.code: item.quantity for item in indicators.municipalities} == {
        "0": 3, "05001": 4, "15000": 5, "99999": 7,
    }
    assert indicators.unknown_department == 3
    assert indicators.unknown_municipality == 8
    assert {item.period: item.quantity for item in indicators.years} == {2023: 3, 2024: 16}
    assert {item.period: item.quantity for item in indicators.months} == {1: 4, 2: 10, 3: 5}
    assert {item.period: item.quantity for item in indicators.weekdays} == {1: 4, 3: 3, 4: 7, 5: 5}
    assert {(item.code, item.year): item.quantity for item in indicators.department_years} == {
        ("0", 2023): 3, ("05", 2024): 4, ("15", 2024): 5, ("99", 2024): 7,
    }
    ranking = rank_regions(indicators.municipalities, indicators.municipality_names, indicators.total)
    assert ranking[0].code == "99999"
    assert next(item for item in ranking if item.code == "15000").percentage == pytest.approx(5 / 19 * 100)
    assert next(item for item in ranking if item.code == "0").name == "SIN ESTABLECER"


def test_indicators_reject_empty_input():
    with pytest.raises(ValueError, match="No hay registros válidos"):
        calculate_indicators(LoadResult([], []))


def test_annual_changes_handle_zero_and_missing_previous_year():
    result = annual_changes([
        PeriodTotal(2024, 8), PeriodTotal(2023, 4), PeriodTotal(2021, 2),
        PeriodTotal(2020, 0), PeriodTotal(2019, 10),
    ])
    assert [item.change_percent for item in result] == [None, -100, None, None, 100]


def test_ranking_zero_total_has_no_percentage():
    result = rank_regions([GeographicTotal("05", 0)], [GeographicName("05", "Antioquia")], 0)
    assert result[0].percentage is None
