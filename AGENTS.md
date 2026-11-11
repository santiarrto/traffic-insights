# Guía para agentes

## Objetivo y alcance

Traffic Insights busca presentar información sobre accidentes de tránsito en Colombia al público general. El primer MVP se ejecutará localmente y utilizará la fuente de lesiones por accidentes de tránsito de datos.gov.co.

El MVP incluirá:

- Carga de archivos CSV descargados y reemplazados manualmente.
- Un indicador del total de víctimas.
- Un mapa con información por departamento y por municipio.
- Información visible sobre la fuente, el periodo y las limitaciones de los datos.

La fuente de accidentes de Acacías se analizará en una etapa posterior y por separado. El despliegue público, la actualización automática, los filtros adicionales, las series temporales y la descarga de resultados no forman parte del MVP actual.

Las ampliaciones posteriores al MVP se detallan en [TASKS.md](TASKS.md).

## Tecnologías

- **Python 3.13** para la preparación y el análisis.
- **DuckDB** para consultar los archivos y calcular indicadores.
- **ijson** para procesar las geometrías GeoJSON de forma incremental.
- **Shapely** para simplificar copias de las geometrías exclusivamente para visualización.
- **Pydeck** para el mapa interactivo.
- **Altair** para los gráficos estadísticos.
- **Streamlit** para el tablero local.
- **pip y un entorno virtual**, con dependencias y configuración del proyecto en `pyproject.toml`.
- **pytest** para las pruebas automatizadas.

Para las geometrías se seleccionaron las capas MGN 2025 del DANE; consultar en el README la comparación de códigos, las limitaciones y las condiciones de uso pendientes de confirmación. Añadir dependencias solo cuando sean necesarias.
Las dependencias resueltas para Python 3.13 en Windows de 64 bits están fijadas en `requirements-lock.txt`; mantenerlo coherente con `pyproject.toml` y verificar la instalación al cambiarlas.

## Estructura del proyecto

La estructura prevista es la siguiente; crear archivos y directorios a medida que se implementen las tareas:

```text
traffic-insights/
├── AGENTS.md
├── README.md
├── TASKS.md
├── PLANNING.md
├── pyproject.toml
├── requirements-lock.txt
├── .gitignore
├── data/
│   ├── raw/              # CSV descargados manualmente
│   └── geo/              # geometrías descargadas
├── src/
│   └── traffic_insights/
│       ├── app.py        # interfaz Streamlit
│       ├── data.py       # carga y validación
│       ├── analysis.py   # consultas y agregaciones
│       ├── geography.py  # relación entre códigos y geometrías
│       ├── download_geography.py # descarga manual paginada
│       ├── charts.py     # visualización de estadísticas
│       └── visualization.py # preparación de la visualización
└── tests/
    └── fixtures/         # datos pequeños y no sensibles para pruebas
```

Los nombres de módulos son una guía inicial, no una obligación de crear archivos vacíos. Mantener la interfaz separada de la carga, los cálculos y la lógica geográfica; adaptar la estructura si la implementación lo requiere sin introducir capas innecesarias.

Los CSV y las geometrías descargados son locales y no deben versionarse. Mantener las reglas de `.gitignore`; las pruebas pueden incluir datos sintéticos pequeños y no sensibles. No modificar los archivos de origen durante la preparación de datos.

## Convenciones de implementación

- Mantener consultas y transformaciones reutilizables fuera de la interfaz Streamlit.
- Preservar los códigos geográficos de forma que no se pierdan ceros iniciales y validar su formato según las fuentes.
- Mantener rutas y configuración local claras; no incorporar credenciales ni depender de rutas personales.
- Agregar pruebas en `tests/` para las validaciones, los cálculos y las uniones geográficas implementadas.
- Documentar comandos de instalación y ejecución solamente después de comprobarlos; no asumir que la estructura prevista ya existe.

## Criterios de trabajo

- No confundir víctimas con accidentes ni sumar registros de fuentes distintas como si midieran lo mismo.
- Revisar definiciones, cobertura, calidad y condiciones de uso antes de interpretar o publicar resultados. No presentar recuentos como tasas de riesgo.
- Validar las entradas y comunicar errores y datos faltantes; no ocultar registros excluidos ni inventar ubicaciones.
- Evitar exponer datos personales y mostrar información agregada adecuada para el público.
- Mantener el README actualizado con instrucciones comprobadas cuando exista una implementación.
- Añadir pruebas para el comportamiento implementado y ejecutar las verificaciones relevantes.

## Gestión de tareas

- Consultar [TASKS.md](TASKS.md) para los roles, estados y criterios de aceptación; actualizar el marcador al cambiar el estado.
- Consultar [PLANNING.md](PLANNING.md) para los prerrequisitos.
- Iniciar una tarea cuando sus dependencias estén completadas. Actualizar ambos archivos cuando cambien las tareas o sus relaciones; los cambios de estado solo se registran en `TASKS.md`.
- Si una decisión pendiente afecta el alcance o la interpretación de los datos, solicitar una definición antes de asumirla.
