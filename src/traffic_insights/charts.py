"""Gráficos de los indicadores de víctimas."""

from datetime import date

import altair as alt
import streamlit as st

from traffic_insights.analysis import VictimIndicators, annual_changes, rank_regions

MONTHS = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
WEEKDAYS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


def render_charts(indicators: VictimIndicators) -> None:
    st.header("Estadísticas de víctimas")
    st.caption(
        "Son recuentos de víctimas registradas, no tasas de riesgo. "
        "La cobertura efectiva de la fuente no está garantizada."
    )
    partial_years = set()
    if indicators.start_date != date(indicators.start_date.year, 1, 1):
        partial_years.add(indicators.start_date.year)
    if indicators.end_date != date(indicators.end_date.year, 12, 31):
        partial_years.add(indicators.end_date.year)
    if partial_years:
        years = ", ".join(str(year) for year in sorted(partial_years))
        st.warning(
            f"El periodo observado no cubre todo el año calendario en: {years}. "
            "Las comparaciones de esos años pueden ser parciales."
        )
    st.caption(
        "Las fechas extremas solo describen los registros disponibles; "
        "no demuestran que los demás periodos estén completos."
    )

    st.subheader("Evolución anual")
    annual = [
        {
            "Año": item.year,
            "Víctimas": item.quantity,
            "Variación": (
                f"{item.change_percent:+.1f} %" if item.change_percent is not None else "No disponible"
            ),
        }
        for item in annual_changes(indicators.years)
    ]
    annual_chart = (
        alt.Chart(alt.Data(values=annual))
        .mark_bar()
        .encode(
            x=alt.X("Año:O", sort="ascending"),
            y=alt.Y("Víctimas:Q"),
            tooltip=["Año:O", "Víctimas:Q", "Variación:N"],
        )
    )
    st.altair_chart(annual_chart, width="stretch", alt="Víctimas registradas por año")
    st.dataframe(annual, hide_index=True)
    st.caption(
        "La variación compara con el año calendario anterior; no se calcula si ese año "
        "no tiene registros o su cantidad es cero."
    )

    st.subheader("Patrones temporales")
    st.caption(
        "Las cantidades suman todos los años disponibles; los periodos sin registros no se muestran."
    )
    columns = st.columns(2)
    for column, title, totals, labels in (
        (columns[0], "Por mes", indicators.months, MONTHS),
        (columns[1], "Por día de la semana", indicators.weekdays, WEEKDAYS),
    ):
        rows = [{"Periodo": labels[item.period - 1], "Víctimas": item.quantity} for item in totals]
        chart = (
            alt.Chart(alt.Data(values=rows))
            .mark_bar()
            .encode(
                x=alt.X("Periodo:N", sort=list(labels), title=title),
                y=alt.Y("Víctimas:Q"),
                tooltip=["Periodo:N", "Víctimas:Q"],
            )
        )
        with column:
            st.altair_chart(chart, width="stretch", alt=f"Víctimas registradas {title.lower()}")

    st.subheader("Ranking geográfico")
    ranking_level = st.radio(
        "Nivel del ranking", ["Departamentos", "Municipios"], horizontal=True
    )
    totals, names = (
        (indicators.departments, indicators.department_names)
        if ranking_level == "Departamentos"
        else (indicators.municipalities, indicators.municipality_names)
    )
    ranking = [
        {
            "Zona": f"{item.name} ({item.code})",
            "Víctimas": item.quantity,
            "Proporción": (
                f"{item.percentage:.2f} %" if item.percentage is not None else "No disponible"
            ),
        }
        for item in rank_regions(totals, names, indicators.total)
    ]
    ranking_chart = (
        alt.Chart(alt.Data(values=ranking[:10]))
        .mark_bar()
        .encode(
            x=alt.X("Víctimas:Q"),
            y=alt.Y("Zona:N", sort="-x", title=None),
            tooltip=["Zona:N", "Víctimas:Q", "Proporción:N"],
        )
    )
    st.altair_chart(ranking_chart, width="stretch", alt="Diez códigos con más víctimas")
    st.caption(
        "El gráfico muestra los diez códigos con mayores cantidades; la tabla incluye todos. "
        "La proporción usa el total nacional, incluidas las ubicaciones no establecidas "
        "(código 0 y, en municipios, códigos terminados en 000). "
        "Si el total es cero, la proporción no está disponible."
    )
    st.dataframe(ranking, hide_index=True)

    st.subheader("Comparación entre departamentos")
    department_names = {item.code: item.name for item in indicators.department_names if item.code != "0"}
    options = sorted(department_names, key=lambda code: (department_names[code], code))
    selected = st.multiselect(
        "Departamentos para comparar", options, default=options[:2],
        format_func=lambda code: f"{department_names[code]} ({code})",
    )
    if not selected:
        st.info("Selecciona al menos un departamento para ver la comparación.")
        return
    selected_set = set(selected)
    comparison = [
        {
            "Año": item.year,
            "Departamento": f"{department_names[item.code]} ({item.code})",
            "Víctimas": item.quantity,
        }
        for item in indicators.department_years if item.code in selected_set
    ]
    comparison_chart = (
        alt.Chart(alt.Data(values=comparison))
        .mark_bar()
        .encode(
            x=alt.X("Año:O", sort="ascending"),
            xOffset="Departamento:N",
            y=alt.Y("Víctimas:Q"),
            color="Departamento:N",
            tooltip=["Año:O", "Departamento:N", "Víctimas:Q"],
        )
    )
    st.altair_chart(comparison_chart, width="stretch", alt="Víctimas por año y departamento")
    st.caption(
        "Solo se muestran combinaciones de año y departamento con registros. "
        "Las cantidades con departamento no establecido no se asignan a otro departamento."
    )
