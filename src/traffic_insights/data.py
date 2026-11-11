"""Carga y validación de los registros de víctimas."""

import csv
import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = (
    "FECHA HECHO",
    "COD_DEPTO",
    "DEPARTAMENTO",
    "COD_MUNI",
    "MUNICIPIO",
    "CANTIDAD",
)


@dataclass(frozen=True, slots=True)
class VictimRecord:
    event_date: date
    department_code: str
    department: str
    municipality_code: str
    municipality: str
    quantity: int


@dataclass(frozen=True, slots=True)
class RejectedRow:
    line: int
    reason: str


@dataclass(slots=True)
class LoadResult:
    records: list[VictimRecord]
    rejected: list[RejectedRow]


def _parse_record(values: dict[str, str]) -> VictimRecord:
    date_text = values["FECHA HECHO"].strip()
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", date_text):
        raise ValueError("FECHA HECHO debe tener el formato dd/mm/aaaa")
    day, month, year = (int(part) for part in date_text.split("/"))
    try:
        event_date = date(year, month, day)
    except ValueError as exc:
        raise ValueError("FECHA HECHO no es una fecha válida") from exc

    department_code = values["COD_DEPTO"].strip()
    municipality_code = values["COD_MUNI"].strip()
    if not re.fullmatch(r"0|[0-9]{2}", department_code):
        raise ValueError("COD_DEPTO debe ser 0 o un código de dos dígitos")
    if not re.fullmatch(r"0|[0-9]{5}", municipality_code):
        raise ValueError("COD_MUNI debe ser 0 o un código de cinco dígitos")
    if (
        department_code != "0"
        and municipality_code != "0"
        and not municipality_code.startswith(department_code)
    ):
        raise ValueError("COD_MUNI no corresponde a COD_DEPTO")

    department = values["DEPARTAMENTO"].strip()
    municipality = values["MUNICIPIO"].strip()
    if not department or not municipality:
        raise ValueError("DEPARTAMENTO y MUNICIPIO no pueden estar vacíos")

    quantity_text = values["CANTIDAD"].strip()
    if not re.fullmatch(r"[0-9]+", quantity_text) or len(quantity_text) > 19:
        raise ValueError("CANTIDAD debe ser un entero no negativo")
    quantity = int(quantity_text)
    if quantity > 2**63 - 1:
        raise ValueError("CANTIDAD supera el máximo admitido")

    return VictimRecord(
        event_date, department_code, department, municipality_code, municipality, quantity
    )


def load_victims_csv(path: str | Path) -> LoadResult:
    """Carga el CSV y devuelve los registros válidos y las filas rechazadas.

    El número de línea de un rechazo corresponde a la última línea física de
    ese registro CSV. Un archivo ausente, ilegible o sin registros válidos
    produce una excepción.
    """
    records: list[VictimRecord] = []
    rejected: list[RejectedRow] = []

    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        try:
            header = next(reader, None)
            if not header:
                raise ValueError("El CSV no contiene encabezados")
            if len(set(header)) != len(header):
                raise ValueError("El CSV contiene encabezados duplicados")
            missing = set(REQUIRED_COLUMNS) - set(header)
            if missing:
                raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

            for row in reader:
                if len(row) != len(header):
                    rejected.append(RejectedRow(reader.line_num, "Número de columnas incorrecto"))
                    continue
                values = dict(zip(header, row, strict=True))
                try:
                    records.append(_parse_record(values))
                except ValueError as exc:
                    rejected.append(RejectedRow(reader.line_num, str(exc)))
        except csv.Error as exc:
            raise ValueError(f"CSV inválido cerca de la línea {reader.line_num}: {exc}") from exc

    if rejected:
        logger.warning("Se rechazaron %d registros del CSV %s", len(rejected), path)
    if not records:
        detail = f"; primer rechazo en línea {rejected[0].line}: {rejected[0].reason}" if rejected else ""
        raise ValueError(f"El CSV no contiene registros válidos{detail}")

    return LoadResult(records, rejected)
