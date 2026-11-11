"""Tablero local de víctimas de accidentes de tránsito."""

from pathlib import Path

import duckdb
import ijson
import pydeck as pdk
import streamlit as st
from shapely.errors import GEOSException

from traffic_insights.analysis import GeographicTotal, VictimIndicators, calculate_indicators
from traffic_insights.charts import render_charts
from traffic_insights.data import load_victims_csv
from traffic_insights.geography import GeographicLevel
from traffic_insights.visualization import display_features, map_view, select_features, style_features


@st.cache_data(show_spinner=False, max_entries=4)
def cached_indicators(path: Path, modified_ns: int, size: int) -> VictimIndicators:
    return calculate_indicators(load_victims_csv(path))


@st.cache_data(show_spinner=False, max_entries=4)
def cached_map(
    path: Path,
    modified_ns: int,
    size: int,
    level: GeographicLevel,
    totals: tuple[GeographicTotal, ...],
) -> tuple[list[dict], tuple[GeographicTotal, ...]]:
    return display_features(path, level, totals)


def file_version(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


def number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def main(data_dir: Path) -> None:
    st.set_page_config(page_title="Traffic Insights", layout="wide")
    st.title("Víctimas de accidentes de tránsito en Colombia")
    st.caption("Recuento de víctimas registradas, no de accidentes ni una tasa de riesgo.")

    csv_files = sorted((data_dir / "raw").glob("*.csv"))
    if not csv_files:
        st.error("No se encontró ningún CSV en data/raw. Descarga allí el archivo de lesiones.")
        st.stop()
    default = next((i for i, path in enumerate(csv_files) if "LESIONES" in path.name.upper()), 0)
    csv_path = st.selectbox("Archivo de víctimas", csv_files, index=default, format_func=lambda p: p.name)
    try:
        with st.spinner("Cargando y validando los registros..."):
            indicators = cached_indicators(csv_path, *file_version(csv_path))
    except (OSError, ValueError, UnicodeError, duckdb.Error, RuntimeError) as exc:
        st.error(f"No se pudo cargar el archivo de víctimas: {exc}")
        st.stop()

    st.metric("Total de víctimas", number(indicators.total))
    st.write(
        f"Periodo de los registros válidos: {indicators.start_date:%d/%m/%Y} "
        f"a {indicators.end_date:%d/%m/%Y}. Registros válidos: {number(indicators.valid_records)}."
    )
    if indicators.rejected:
        st.warning(f"Se excluyeron {number(len(indicators.rejected))} registros inválidos.")
        with st.expander("Ver líneas y motivos de rechazo"):
            st.dataframe(
                [{"Línea": row.line, "Motivo": row.reason} for row in indicators.rejected],
                hide_index=True,
            )
    else:
        st.caption("No se rechazaron registros.")

    level_label = st.radio("Nivel geográfico", ["Departamentos", "Municipios"], horizontal=True)
    geo_dir = data_dir / "geo"
    department_path = geo_dir / "departamentos_2025.geojson"
    try:
        with st.spinner("Preparando el mapa departamental; la primera carga puede tardar varios minutos..."):
            departments, department_unmatched = cached_map(
                department_path, *file_version(department_path), "department", indicators.departments
            )

        if level_label == "Municipios":
            names = {
                feature["properties"]["dpto_ccdgo"]: feature["properties"]["dpto_cnmbr"]
                for feature in departments
            }
            department = st.selectbox(
                "Departamento", sorted(names, key=lambda code: names[code]),
                format_func=lambda code: f"{names[code]} ({code})",
            )
            municipality_path = geo_dir / "municipios_2025.geojson"
            with st.spinner("Preparando el mapa municipal; la primera carga puede tardar varios minutos..."):
                municipalities, unmatched = cached_map(
                    municipality_path, *file_version(municipality_path),
                    "municipality", indicators.municipalities,
                )
            features = select_features(municipalities, department)
            level: GeographicLevel = "municipality"
        else:
            features = departments
            unmatched = department_unmatched
            level = "department"

        styled = style_features(features, level)
        longitude, latitude, zoom = map_view(styled)
        layer = pdk.Layer(
            "GeoJsonLayer", {"type": "FeatureCollection", "features": styled},
            pickable=True, filled=True, stroked=True,
            get_fill_color="properties.map_color", get_line_color=[80, 80, 80, 180],
            line_width_min_pixels=0.5,
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=pdk.ViewState(longitude=longitude, latitude=latitude, zoom=zoom),
                map_style=None,
                tooltip={"text": "{map_name}\nVíctimas: {map_count}"},
            ),
            alt="Mapa de víctimas por zona geográfica",
        )
    except (OSError, ValueError, KeyError, UnicodeError, ijson.JSONError, GEOSException) as exc:
        st.error(f"No se pudo preparar el mapa: {exc}")
        st.stop()

    st.caption(
        "Gris: sin registros; amarillo a rojo: cantidades crecientes en escala logarítmica "
        "para la vista mostrada. Pasa el cursor por una zona para ver su cantidad."
    )
    unmatched_quantity = sum(item.quantity for item in unmatched)
    st.warning(
        f"En el nivel {'departamental' if level == 'department' else 'municipal'}, "
        f"{number(unmatched_quantity)} víctimas de todo el país no tienen geometría "
        f"correspondiente ({number(len(unmatched))} códigos). Están incluidas en el total."
    )
    if unmatched:
        with st.expander("Ver códigos sin geometría"):
            st.dataframe(
                [{"Código": item.code, "Víctimas": item.quantity} for item in unmatched],
                hide_index=True,
            )
    st.info(
        "Los contornos son aproximados y se simplifican solo para visualización. "
        "Los límites DANE de 2025 no necesariamente representan los límites históricos. "
        "La cobertura y la calidad dependen de la fuente."
    )
    st.markdown(
        "Fuente de víctimas: [Lesiones accidentes de tránsito, MinDefensa / datos.gov.co]"
        "(https://www.datos.gov.co/Seguridad-y-Defensa/LESIONES-ACCIDENTES-DE-TR-NSITO/ntej-qq7v). "
        "Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co. "
        "Las condiciones específicas de las capas deben confirmarse antes de publicarlas."
    )
    render_charts(indicators)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[2] / "data")
