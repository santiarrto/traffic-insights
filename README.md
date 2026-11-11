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

Los resultados dependen de la calidad y cobertura de los datos; un mayor número de registros no implica necesariamente un mayor riesgo.

## Vistas del tablero

Las capturas muestran el archivo local examinado; los resultados cambian al actualizar los datos.

### Total y mapa departamental

Total de víctimas, periodo disponible y distribución por departamento. Al pasar el cursor se consulta la cantidad de una zona.

![Total de víctimas y mapa departamental de Colombia](docs/images/captura%201.png)

### Mapa municipal

Distribución por municipio dentro del departamento seleccionado; el ejemplo muestra Antioquia.

![Mapa de víctimas por municipio en Antioquia](docs/images/captura%202.png)

### Evolución anual

Víctimas por año, variación respecto al año anterior y advertencia sobre periodos observados parciales.

![Gráfico y tabla de evolución anual de víctimas](docs/images/captura%203.png)

### Patrones temporales

Recuentos agregados por mes y por día de la semana para todos los años disponibles.

![Gráficos de víctimas por mes y día de la semana](docs/images/captura%204.png)

### Ranking geográfico

Los diez códigos con mayores recuentos, con opción de consultar departamentos o municipios.

![Ranking de víctimas por departamento](docs/images/captura%205.png)

### Comparación entre departamentos

Comparación anual de los departamentos seleccionados; el ejemplo incluye Antioquia, Bogotá D.C. y Valle del Cauca.

![Comparación anual de víctimas entre tres departamentos](docs/images/captura%206.png)

Las capturas del mapa usan geometrías del DANE y mapa base de OpenStreetMap/CARTO. Antes de publicarlas, confirmar las condiciones específicas de uso descritas en [Geometrías para el mapa](#geometrías-para-el-mapa).

## Fuentes de datos

- [Accidentes Viales](https://www.datos.gov.co/Transporte/Accidentes-Viales/yu3i-jau4/about_data): accidentes registrados en el municipio de Acacías, Meta. Incluye fecha, ubicación, vehículos involucrados, heridos y muertes.
- [Lesiones accidentes de tránsito](https://www.datos.gov.co/Seguridad-y-Defensa/LESIONES-ACCIDENTES-DE-TR-NSITO/ntej-qq7v/about_data): datos medidos en víctimas, con fecha, departamento, municipio y cantidad.

La primera fuente no representa todo el país. Los accidentes y las víctimas son unidades de medida distintas: no se deben sumar ni comparar directamente como si fueran equivalentes. Antes de publicar indicadores, se revisarán la cobertura temporal y geográfica, las definiciones, la calidad de los datos y las condiciones de uso de cada fuente.

### Fuente prioritaria: lesiones en accidentes de tránsito

Según los [metadatos de datos.gov.co](https://www.datos.gov.co/api/views/ntej-qq7v.json), consultados el 11 de noviembre de 2026:

- **Entidad:** Ministerio de Defensa Nacional - MinDefensa, Bogotá D.C.
- **Medida:** la descripción de la fuente indica que se mide en víctimas; los metadatos no detallan cómo se construye cada registro ni definen los campos.
- **Cobertura y actualización declaradas:** nacional y mensual. La actualización de datos registrada en los metadatos es del 21 de octubre de 2026 a las 14:45 UTC.
- **Licencia declarada:** [Creative Commons Atribución-CompartirIgual 4.0 Internacional](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Revisar sus condiciones para el uso y la publicación previstos.

| Campo en los metadatos | Tipo | Descripción disponible |
| --- | --- | --- |
| `FECHA HECHO` | Fecha | Fecha del hecho; en el CSV examinado usa `dd/mm/aaaa`. |
| `COD_DEPTO` | Texto | Código de departamento; conservar ceros iniciales y tratar `0` como ubicación no establecida. |
| `DEPARTAMENTO` | Texto | Nombre del departamento. |
| `COD_MUNI` | Texto | Código de municipio; conservar ceros iniciales y tratar `0` como ubicación no establecida. |
| `MUNICIPIO` | Texto | Nombre del municipio. |
| `CANTIDAD` | Número | Cantidad asociada al registro; la fuente indica que la medida es víctimas, pero no detalla cómo se construye cada registro. |

Revisión del archivo local `data/raw/LESIONES_ACCIDENTES_DE_TRÁNSITO_20261111.csv`, realizada el 11 de noviembre de 2026:

- Contiene 644.042 filas, con fechas entre el 1 de enero de 2003 y el 30 de septiembre de 2026. La suma de `CANTIDAD` es 885.829; es un recuento de la fuente, no una tasa de riesgo.
- No se observaron campos vacíos, fechas inválidas en el formato indicado ni cantidades negativas o no enteras.
- Hay 294.354 filas idénticas a una fila anterior en los seis campos disponibles. No hay un identificador de víctima o hecho que permita concluir que sean duplicados indebidos: no eliminarlas automáticamente.
- Hay 34 códigos de departamento y 1.089 de municipio distintos, incluido el código `0` de ubicación **SIN ESTABLECER**. Este aparece en tres filas con una cantidad total de cinco; las demás filas tienen códigos de dos y cinco dígitos, respectivamente. La comparación con las capas seleccionadas se describe abajo.

Estas observaciones describen únicamente el archivo examinado, no garantizan la cobertura efectiva ni la ausencia de otros problemas de calidad. La descarga directa falló durante la revisión con errores HTTP 500 y 503; el archivo analizado fue suministrado localmente.

### Geometrías para el mapa

Se seleccionaron las capas del Marco Geoestadístico Nacional (MGN) 2025 publicadas en el catálogo del DANE: [departamentos](https://services.arcgis.com/ioNRSZMYYlx0PUaB/arcgis/rest/services/MGN2025_DPTO_POLITICO/FeatureServer/0) y [municipios](https://services.arcgis.com/ioNRSZMYYlx0PUaB/arcgis/rest/services/MGN2025_MPIO_GRAFICO/FeatureServer/0). Las capas se descargaron en GeoJSON con coordenadas WGS84 y se validaron sus códigos, estructura de polígonos, anillos y rangos de coordenadas; no se ha verificado su topología.

- **Unión:** comparar `COD_DEPTO` con `dpto_ccdgo` y `COD_MUNI` con `mpio_cdpmp`, como texto y sin eliminar ceros iniciales. No unir por nombre.
- **Cobertura observada:** las capas consultadas el 11 de noviembre de 2026 contienen 33 códigos departamentales y 1.122 municipales únicos. En el CSV examinado, el código departamental `0` no coincide: representa tres filas y cinco víctimas sin ubicación establecida.
- **Municipios sin correspondencia:** además del código `0`, aparecen `15000`, `25000`, `27000`, `52000` y `88000`, todos con municipio **SIN ESTABLECER**. En total son 11 filas y 14 víctimas sin geometría municipal; ocho de esas filas, con nueve víctimas, sí tienen departamento identificable.
- **Tratamiento:** conservar todas las cantidades en el total general; incluir en el mapa departamental los registros con departamento válido y en el municipal solo los que tengan municipio válido. Informar por separado las cantidades no representadas en cada nivel y no inventar ubicaciones ni eliminar filas idénticas.
- **Limitación temporal:** una geometría de 2025 aplicada a datos de 2003 a 2026 no representa necesariamente los límites históricos de cada fecha.

Las fichas de estas capas no declaran una licencia específica. Los [términos generales del DANE](https://www.dane.gov.co/index.php/terminos-y-condiciones) autorizan el uso y la transformación de información del portal con la cita textual «Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co». Debe confirmarse su aplicación a estas capas y cualquier condición adicional antes de redistribuirlas o publicar el tablero.

## Enfoque tecnológico

- **Python** para la preparación y el análisis de datos.
- **DuckDB** para consultar los archivos y calcular indicadores.
- **Streamlit** para construir un tablero web interactivo.
- **Altair** para los gráficos estadísticos.

Este enfoque permite validar el producto rápidamente. La forma de despliegue está pendiente de definición; la actualización automática de los archivos podrá evaluarse más adelante.

## Preparación local

Se requieren [Python 3.13](https://www.python.org/downloads/), pip y conexión a internet para instalar dependencias y descargar los datos. El mapa base también necesita conexión. La instalación y el archivo de versiones se comprobaron en Windows de 64 bits; macOS y Linux no se han probado.

Descarga el repositorio como ZIP o clónalo con Git, y abre una terminal en la raíz del proyecto:

```text
git clone https://github.com/santiarrto/traffic-insights.git
cd traffic-insights
```

La versión descargada debe incluir `pyproject.toml` y `src/traffic_insights/app.py`. Si trabajas con una copia existente, entra directamente en su carpeta.

### Instalar dependencias

En Windows (PowerShell), comprueba que `python --version` indique Python 3.13 y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-lock.txt -e '.[dev]'
.\.venv\Scripts\python.exe -m pip check
New-Item -ItemType Directory -Force -Path 'data\raw','data\geo'
```

Si `python` no está en el PATH, usa la ruta de Python 3.13 para crear el entorno; por ejemplo, si se instaló en la ubicación de usuario predeterminada:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
```

En macOS o Linux, comprueba que `python3.13 --version` funcione y ejecuta:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip check
mkdir -p data/raw data/geo
```

En macOS y Linux se instalan las versiones directas fijadas en `pyproject.toml`; las dependencias indirectas se resuelven para la plataforma, ya que `requirements-lock.txt` se verificó solo en Windows.

### Descargar y ubicar los datos

Crear las carpetas `data/raw/` y `data/geo/` si aún no existen. Los archivos descargados y generados son locales y no se versionan.

1. Descargar el [CSV completo de lesiones](https://www.datos.gov.co/api/views/ntej-qq7v/rows.csv?accessType=DOWNLOAD) desde datos.gov.co y guardarlo en `data/raw/`. El tablero permite seleccionarlo por nombre y prioriza uno que contenga `LESIONES`. La fuente ha presentado errores de descarga; si ocurre, intentar más tarde.
2. Descargar la [capa departamental GeoJSON](https://services.arcgis.com/ioNRSZMYYlx0PUaB/arcgis/rest/services/MGN2025_DPTO_POLITICO/FeatureServer/0/query?where=1%3D1&outFields=dpto_ccdgo%2Cdpto_cnmbr&outSR=4326&resultRecordCount=2000&f=geojson) del DANE. Guardar la descarga completa como `data/geo/departamentos_2025.geojson`. La consulta tiene un límite de 2.000 geometrías y debe revisarse si cambia la cobertura del servicio.
3. Desde la raíz del proyecto, ejecutar el comando correspondiente para descargar la capa municipal por páginas y guardarla como `data/geo/municipios_2025.geojson`.

   Windows (PowerShell):

   ```powershell
   .\.venv\Scripts\python.exe -m traffic_insights.download_geography data\geo\municipios_2025.geojson
   ```

   macOS o Linux:

   ```sh
   .venv/bin/python -m traffic_insights.download_geography data/geo/municipios_2025.geojson
   ```

   La capa ocupa aproximadamente 229 MB y puede tardar varios minutos. El comando comprueba el conteo, los códigos y la estructura de las geometrías; solo reemplaza el destino si termina correctamente. Si falla una página, muestra el error y puede ejecutarse de nuevo. La validación no comprueba la topología.

No reemplazar el archivo departamental por una descarga incompleta. Si el servicio devuelve un error, JSON truncado o marca la capa como incompleta, el tablero mostrará el problema.

Para actualizar datos, descargar el CSV o las capas de nuevo y reemplazar los archivos correspondientes. La aplicación detecta cambios de tamaño o fecha de modificación y recalcula los indicadores y mapas. También se puede elegir otro CSV dentro de `data/raw/`. Los nombres de las dos capas deben conservarse.

### Ejecutar el tablero

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\traffic_insights\app.py
```

macOS o Linux:

```sh
.venv/bin/python -m streamlit run src/traffic_insights/app.py
```

Abrir la dirección local indicada por Streamlit. Elegir el archivo de víctimas y el nivel geográfico; en municipios, seleccionar además un departamento. Pasar el cursor sobre una zona muestra su nombre y cantidad. Detener la aplicación con `Ctrl+C`.

La primera carga de cada nivel puede tardar mientras se validan y simplifican las geometrías; los resultados se conservan en caché durante la ejecución. Los contornos se simplifican con una tolerancia de 0,001 grados para mostrarlos, no modifican las capas originales y son aproximados. Solo se envían al navegador los municipios del departamento seleccionado. El mapa base de Streamlit utiliza teselas de CARTO/OpenStreetMap, por lo que requiere conexión para mostrarlas.

El gris significa que no hay registros para esa geometría, no necesariamente cero víctimas. Los tonos amarillos a rojos representan cantidades crecientes en escala logarítmica, recalculada para cada vista; no permiten comparar directamente colores entre vistas. Las cantidades sin geometría corresponden a todo el país y permanecen en el total general. El tablero informa también los registros rechazados.

En **Estadísticas de víctimas** se muestran la evolución anual y su variación, los totales por mes y día de la semana, y rankings por departamento o municipio. El gráfico del ranking presenta los diez códigos con mayores cantidades y la tabla incluye todos; las proporciones usan el total nacional, incluidas las ubicaciones no establecidas. Se pueden seleccionar varios departamentos para comparar sus recuentos anuales.

Los gráficos usan la suma de `CANTIDAD` de los registros válidos, sin eliminar filas idénticas. Las distribuciones por mes y día reúnen todos los años; los periodos sin registros no se muestran. Una variación anual no está disponible si no hay registros del año anterior o si su cantidad es cero; una proporción tampoco se calcula si el total nacional es cero. Las fechas extremas pueden indicar años parcialmente observados, pero no garantizan la integridad de los demás periodos. Estos recuentos no son tasas de riesgo.

### Carga de datos

El módulo `traffic_insights.data` ofrece `load_victims_csv(ruta)`. Devuelve registros válidos y filas rechazadas con su línea y motivo; además, registra una advertencia si hay rechazos. La carga conserva ceros iniciales, ubicaciones no establecidas y filas idénticas. Un archivo ausente, un CSV ilegible, encabezados inválidos o la ausencia de registros válidos producen un error explícito.

El módulo `traffic_insights.analysis` ofrece `calculate_indicators(resultado_de_carga)`. Calcula con DuckDB el total, el periodo y los agregados por código de departamento y municipio, y conserva los rechazos. También informa las cantidades con códigos de ubicación no establecida: `0` para departamentos y `0` o códigos terminados en `000` para municipios. Estas cantidades están incluidas en el total y los agregados; otras diferencias con las geometrías se identificarán al preparar el mapa.

El módulo `traffic_insights.geography` ofrece `prepare_map(origen, salida, nivel, agregados)`. Lee GeoJSON de forma incremental, escribe una copia enriquecida con `victim_count` y devuelve los códigos y cantidades sin geometría. Las geometrías sin registros tienen `victim_count: null`, no cero. Los archivos locales descargados y generados están en `data/geo/` y no se versionan:

| Nivel | Origen | Salida preparada |
| --- | --- | --- |
| Departamentos | `departamentos_2025.geojson` | `departamentos_mapa.geojson` |
| Municipios | `municipios_2025.geojson` | `municipios_mapa.geojson` |

El archivo municipal de origen ocupa aproximadamente 229 MB. La redistribución o publicación requiere confirmar primero las condiciones de uso de las capas.

Para ejecutar las pruebas en Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests
```

En macOS o Linux:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider tests
```

## Estado

El tablero local, la carga de datos, los indicadores y la preparación geográfica están implementados.

El alcance y las reglas para agentes están en [AGENTS.md](AGENTS.md); las tareas y sus prerrequisitos se encuentran en [TASKS.md](TASKS.md) y [PLANNING.md](PLANNING.md).
