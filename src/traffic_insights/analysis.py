"""Cálculo de indicadores a partir de registros validados."""

from dataclasses import dataclass
from datetime import date
from typing import Sequence

import duckdb

from traffic_insights.data import LoadResult, RejectedRow


@dataclass(frozen=True, slots=True)
class GeographicTotal:
    code: str
    quantity: int


@dataclass(frozen=True, slots=True)
class GeographicName:
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class PeriodTotal:
    period: int
    quantity: int


@dataclass(frozen=True, slots=True)
class DepartmentYearTotal:
    code: str
    year: int
    quantity: int


@dataclass(frozen=True, slots=True)
class AnnualChange:
    year: int
    quantity: int
    change_percent: float | None


@dataclass(frozen=True, slots=True)
class RankedRegion:
    code: str
    name: str
    quantity: int
    percentage: float | None


@dataclass(frozen=True, slots=True)
class VictimIndicators:
    total: int
    start_date: date
    end_date: date
    valid_records: int
    rejected: tuple[RejectedRow, ...]
    departments: tuple[GeographicTotal, ...]
    municipalities: tuple[GeographicTotal, ...]
    unknown_department: int
    unknown_municipality: int
    department_names: tuple[GeographicName, ...]
    municipality_names: tuple[GeographicName, ...]
    years: tuple[PeriodTotal, ...]
    months: tuple[PeriodTotal, ...]
    weekdays: tuple[PeriodTotal, ...]
    department_years: tuple[DepartmentYearTotal, ...]


def annual_changes(years: Sequence[PeriodTotal]) -> tuple[AnnualChange, ...]:
    """Compara únicamente años consecutivos con una base anterior positiva."""
    previous = None
    results = []
    for item in sorted(years, key=lambda value: value.period):
        change = None
        if previous is not None and previous.period == item.period - 1 and previous.quantity > 0:
            change = (item.quantity - previous.quantity) / previous.quantity * 100
        results.append(AnnualChange(item.period, item.quantity, change))
        previous = item
    return tuple(results)


def rank_regions(
    totals: Sequence[GeographicTotal], names: Sequence[GeographicName], national_total: int
) -> tuple[RankedRegion, ...]:
    """Ordena las zonas e incluye los códigos sin ubicación en el denominador."""
    names_by_code = {item.code: item.name for item in names}
    return tuple(
        RankedRegion(
            item.code, names_by_code[item.code], item.quantity,
            item.quantity / national_total * 100 if national_total else None,
        )
        for item in sorted(totals, key=lambda value: (-value.quantity, value.code))
    )


def calculate_indicators(data: LoadResult) -> VictimIndicators:
    """Calcula totales sin descartar registros por falta de ubicación."""
    if not data.records:
        raise ValueError("No hay registros válidos para calcular indicadores")

    with duckdb.connect() as connection:
        connection.execute(
            """
            CREATE TABLE victims (
                event_date DATE,
                department_code VARCHAR,
                department VARCHAR,
                municipality_code VARCHAR,
                municipality VARCHAR,
                quantity BIGINT
            )
            """
        )
        for start in range(0, len(data.records), 8192):
            batch = [
                {
                    "event_date": record.event_date,
                    "department_code": record.department_code,
                    "department": record.department,
                    "municipality_code": record.municipality_code,
                    "municipality": record.municipality,
                    "quantity": record.quantity,
                }
                for record in data.records[start : start + 8192]
            ]
            connection.execute(
                """
                INSERT INTO victims
                SELECT r.event_date, r.department_code, r.department,
                       r.municipality_code, r.municipality, r.quantity
                FROM UNNEST(?) AS t(r)
                """,
                [batch],
            )

        totals = connection.execute(
            """
            SELECT SUM(quantity), MIN(event_date), MAX(event_date), COUNT(*),
                COALESCE(SUM(quantity) FILTER (WHERE department_code = '0'), 0),
                COALESCE(SUM(quantity) FILTER (
                    WHERE municipality_code = '0' OR
                          (LENGTH(municipality_code) = 5 AND RIGHT(municipality_code, 3) = '000')
                ), 0)
            FROM victims
            """
        ).fetchone()
        if totals is None:
            raise RuntimeError("DuckDB no devolvió los indicadores")

        departments = connection.execute(
            """
            SELECT department_code, SUM(quantity)
            FROM victims GROUP BY department_code ORDER BY department_code
            """
        ).fetchall()
        municipalities = connection.execute(
            """
            SELECT municipality_code, SUM(quantity)
            FROM victims GROUP BY municipality_code ORDER BY municipality_code
            """
        ).fetchall()
        department_names = connection.execute(
            """
            SELECT department_code, string_agg(DISTINCT department, ' / ' ORDER BY department)
            FROM victims GROUP BY department_code ORDER BY department_code
            """
        ).fetchall()
        municipality_names = connection.execute(
            """
            SELECT municipality_code, string_agg(DISTINCT municipality, ' / ' ORDER BY municipality)
            FROM victims GROUP BY municipality_code ORDER BY municipality_code
            """
        ).fetchall()
        years = connection.execute(
            """
            SELECT YEAR(event_date), SUM(quantity)
            FROM victims GROUP BY 1 ORDER BY 1
            """
        ).fetchall()
        months = connection.execute(
            """
            SELECT MONTH(event_date), SUM(quantity)
            FROM victims GROUP BY 1 ORDER BY 1
            """
        ).fetchall()
        weekdays = connection.execute(
            """
            SELECT ISODOW(event_date), SUM(quantity)
            FROM victims GROUP BY 1 ORDER BY 1
            """
        ).fetchall()
        department_years = connection.execute(
            """
            SELECT department_code, YEAR(event_date), SUM(quantity)
            FROM victims GROUP BY 1, 2 ORDER BY 1, 2
            """
        ).fetchall()

    return VictimIndicators(
        total=totals[0],
        start_date=totals[1],
        end_date=totals[2],
        valid_records=totals[3],
        rejected=tuple(data.rejected),
        departments=tuple(GeographicTotal(*row) for row in departments),
        municipalities=tuple(GeographicTotal(*row) for row in municipalities),
        unknown_department=totals[4],
        unknown_municipality=totals[5],
        department_names=tuple(GeographicName(*row) for row in department_names),
        municipality_names=tuple(GeographicName(*row) for row in municipality_names),
        years=tuple(PeriodTotal(*row) for row in years),
        months=tuple(PeriodTotal(*row) for row in months),
        weekdays=tuple(PeriodTotal(*row) for row in weekdays),
        department_years=tuple(DepartmentYearTotal(*row) for row in department_years),
    )
