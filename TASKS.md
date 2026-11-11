# Tareas

MVP local y tareas posteriores. Las dependencias están en [PLANNING.md](PLANNING.md).

Estados: `[ ]` pendiente, `[~]` en curso, `[!]` bloqueada y `[x]` completada. Registrar el motivo junto a una tarea bloqueada; marcarla como completada solo cuando cumpla su criterio de aceptación.

Los roles agrupan responsabilidades, no implican personas o agentes específicos.

| Estado | ID | Rol | Tarea | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| `[x]` | T01 | Análisis de datos | Examinar la fuente de víctimas | Documentar campos, unidad de medida, cobertura, calidad y condiciones de uso; explicar fecha, cantidad y códigos geográficos. |
| `[x]` | T02 | Geodatos | Evaluar geometrías | Seleccionar una fuente para ambos niveles; documentar cobertura, condiciones de uso, unión por códigos y tratamiento de diferencias. |
| `[x]` | T03 | Plataforma | Preparar el proyecto | Configurar `pyproject.toml` y un entorno local reproducible con las dependencias necesarias. |
| `[x]` | T04 | Ingeniería de datos | Cargar y validar el CSV | Leer el archivo local, validar los campos y valores necesarios e informar errores y registros excluidos. |
| `[x]` | T05 | Ingeniería de datos | Calcular indicadores | Calcular el total de víctimas y agregados por departamento y municipio, conservando el periodo; comprobarlos con datos de prueba. |
| `[x]` | T06 | Geodatos | Preparar el mapa | Unir agregados y geometrías en ambos niveles e informar códigos sin correspondencia, sin inventar ubicaciones. |
| `[x]` | T07 | Aplicación | Construir el tablero | Mostrar el total y un mapa con ambos niveles, junto con fuente, periodo y limitaciones. |
| `[x]` | T08 | Calidad | Verificar el MVP | Probar el flujo local, cálculos, uniones geográficas y errores con casos representativos. |
| `[x]` | T09 | Documentación | Documentar el uso local | Actualizar el README con instrucciones verificadas de instalación, descarga, ubicación y actualización del CSV, ejecución y limitaciones. |
| `[x]` | T10 | Análisis de datos y aplicación | Agregar gráficos de víctimas | Mostrar evolución anual, patrones temporales, rankings geográficos y comparación entre departamentos, con pruebas y limitaciones visibles. |

## Detalle de las tareas

### T01 — Examinar la fuente de víctimas

- Revisar los metadatos y una descarga del CSV de lesiones de datos.gov.co.
- Identificar formato, campos, significado de la cantidad y códigos, cobertura temporal y geográfica, valores faltantes y posibles duplicados.
- Registrar la procedencia, fecha de consulta, condiciones de uso y limitaciones conocidas en el README. Señalar las dudas que requieran una decisión antes de interpretar los datos.
- **Resultado:** metadatos y revisión del CSV local documentados en el README, incluidas las filas idénticas y las ubicaciones no establecidas. La correspondencia geográfica se evaluará en T02.

### T02 — Evaluar geometrías

- Buscar geometrías de departamentos y municipios compatibles con la cobertura y los códigos identificados en T01.
- Revisar su procedencia, licencia, formato y versión; comparar códigos y documentar las diferencias o zonas sin correspondencia.
- Seleccionar y documentar una fuente y una estrategia de unión y tratamiento de diferencias; si no es posible, bloquear la tarea explicando el motivo.
- **Resultado:** seleccionadas las capas MGN 2025 del DANE. La comparación de códigos, advertencias y estrategia están en el README; T06 debe descargar y validar las geometrías completas. Confirmar las condiciones específicas antes de redistribuir las capas o publicar el tablero.

### T03 — Preparar el proyecto

- Definir una versión compatible de Python y declarar en `pyproject.toml` las dependencias necesarias para el MVP y las pruebas.
- Preparar la estructura modular prevista en [AGENTS.md](AGENTS.md) sin crear módulos vacíos innecesarios.
- Comprobar la instalación en un entorno virtual y mantener fuera de Git los datos descargados y archivos generados.
- **Resultado:** Python 3.13, dependencias fijadas y paquete inicial configurados; instalación comprobada en un entorno limpio de Windows de 64 bits.

### T04 — Cargar y validar el CSV

- Leer el CSV descargado manualmente desde una ubicación local documentable, sin modificar el archivo de origen.
- Validar campos requeridos, fechas, cantidades y códigos según lo identificado en T01, preservando los ceros iniciales.
- Informar errores y registros excluidos; probar archivo ausente, columnas faltantes y valores inválidos con datos sintéticos.
- **Resultado:** cargador y pruebas implementados. El CSV local examinado produjo 644.042 registros válidos, sin rechazos, y su contenido no cambió.

### T05 — Calcular indicadores

- Usar DuckDB para calcular el total de víctimas y los agregados por departamento y municipio a partir de los datos validados.
- Conservar el periodo cubierto e identificar registros que no puedan atribuirse a una zona, sin sumarlos dos veces ni ocultarlos.
- Comprobar los resultados con ejemplos conocidos, incluidos registros con cantidades mayores que uno y códigos faltantes.
- **Resultado:** indicadores y pruebas implementados. El CSV local produjo 885.829 víctimas, cinco sin departamento y 14 sin municipio establecido; las diferencias adicionales con geometrías se evaluarán en T06.

### T06 — Preparar el mapa

- Cargar las geometrías seleccionadas en T02 y relacionarlas con los agregados mediante los códigos validados.
- Preparar datos para ambos niveles y registrar las diferencias o códigos sin correspondencia según la estrategia acordada.
- Probar uniones correctas, códigos no encontrados y preservación de ceros iniciales; no inventar ubicaciones.
- **Resultado:** 33 geometrías departamentales y 1.122 municipales procesadas; cinco víctimas sin geometría departamental y 14 sin geometría municipal. La validación es estructural, no topológica.

### T07 — Construir el tablero

- Implementar la interfaz local en Streamlit mostrando el total y un mapa que permita consultar departamentos y municipios.
- Mostrar fuente, periodo, unidad de medida, limitaciones y advertencias relevantes, incluidas las diferencias geográficas detectadas.
- Resolver la interacción entre niveles con base en los datos disponibles y verificar que los errores sean visibles para quien use el tablero.
- **Resultado:** tablero Streamlit con selector de nivel y, para municipios, departamento; geometrías simplificadas solo para visualización y advertencias explícitas.

### T08 — Verificar el MVP

- Ejecutar las pruebas automatizadas y comprobar el flujo local desde la carga hasta la visualización con datos representativos.
- Verificar total, agregados, ambos niveles del mapa y comunicación de datos inválidos o sin correspondencia.
- Registrar los problemas encontrados y corregirlos antes de marcar la tarea como completada.
- **Resultado:** flujo y ambos mapas comprobados con el CSV local y datos sintéticos, incluidos rechazos, geometrías faltantes y reemplazo de datos. El CSV local suma 885.829 víctimas; cinco no se representan por departamento y 14 por municipio.

### T09 — Documentar el uso local

- Actualizar el README con requisitos, instalación y ejecución comprobados en un entorno local.
- Explicar cómo descargar, ubicar y reemplazar el CSV y las geometrías, sin incluirlos en Git.
- Documentar fuentes, periodo y cobertura, unidad de medida, limitaciones, advertencias y procedimiento para ejecutar las pruebas.
- **Resultado:** instrucciones de instalación, descarga, actualización, ejecución y pruebas documentadas. Descarga completa del CSV y de ambas capas verificada; la capa municipal se descargó por páginas y se validaron sus 1.122 geometrías y códigos.

### T10 — Agregar gráficos de víctimas (posterior al MVP)

- Mostrar víctimas por año y variación frente al año anterior; indicar cuando no sea posible calcular la variación, por ejemplo, si el valor anterior es cero.
- Mostrar la distribución de víctimas por mes y por día de la semana.
- Presentar rankings de departamentos y municipios con sus cantidades y proporciones del total; explicar el denominador y las ubicaciones no establecidas.
- Permitir comparar la evolución anual de varios departamentos.
- Señalar periodos observados parciales sin asumir que los demás estén completos; aclarar que son recuentos de víctimas, no tasas de riesgo.
- Probar cálculos y casos de datos faltantes o periodos parciales con datos sintéticos, y actualizar el README con el uso y las limitaciones.
- **Resultado:** gráficos y tablas implementados, con selección de nivel y departamentos. Cálculos, casos límite y visualización comprobados con datos sintéticos y el CSV local.

## Decisiones pendientes

- Confirmar las condiciones de uso específicas de las capas geográficas antes de su redistribución o de publicar el tablero.
