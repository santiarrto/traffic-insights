# Traffic Insights

Proyecto para que el público general explore información sobre accidentes de tránsito en Colombia y obtenga insights a partir de archivos planos.

## Objetivo

Transformar datos de accidentes en información visual y fácil de consultar, con la posibilidad de identificar patrones por ubicación, fecha y otras variables disponibles en los archivos.

## Alcance inicial propuesto

- Cargar archivos CSV descargados y reemplazados manualmente desde las fuentes públicas.
- Validar y preparar los datos antes de analizarlos.
- Priorizar un tablero local con un total de víctimas y un mapa por departamento y municipio.
- Dejar el análisis de accidentes en Acacías para una etapa posterior y mantenerlo separado del tablero de víctimas.
- Documentar las fuentes, su cobertura y las limitaciones de los datos.

Las métricas concretas están por definir. Los resultados dependerán de la calidad y cobertura de los datos; un mayor número de registros no implica necesariamente un mayor riesgo.

## Fuentes de datos

- [Accidentes Viales](https://www.datos.gov.co/Transporte/Accidentes-Viales/yu3i-jau4/about_data): accidentes registrados en el municipio de Acacías, Meta. Incluye fecha, ubicación, vehículos involucrados, heridos y muertes.
- [Lesiones accidentes de tránsito](https://www.datos.gov.co/Seguridad-y-Defensa/LESIONES-ACCIDENTES-DE-TR-NSITO/ntej-qq7v/about_data): datos medidos en víctimas, con fecha, departamento, municipio y cantidad.

La primera fuente no representa todo el país. Los accidentes y las víctimas son unidades de medida distintas: no se deben sumar ni comparar directamente como si fueran equivalentes. Antes de publicar indicadores, se revisarán la cobertura temporal y geográfica, las definiciones, la calidad de los datos y las condiciones de uso de cada fuente.

## Enfoque tecnológico

- **Python** para la preparación y el análisis de datos.
- **DuckDB** para consultar los archivos y calcular indicadores.
- **Streamlit** para construir un tablero web interactivo.

Este enfoque permite validar el producto rápidamente. La forma de despliegue está pendiente de definición; la actualización automática de los archivos podrá evaluarse más adelante.

## Estado

Proyecto en definición. Se han elegido las tecnologías y las fuentes iniciales, pero todavía no hay una implementación ni instrucciones de ejecución.

El alcance y las reglas para agentes están en [AGENTS.md](AGENTS.md); las tareas y sus prerrequisitos se encuentran en [TASKS.md](TASKS.md) y [PLANNING.md](PLANNING.md).
