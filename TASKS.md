# Tareas

El MVP se desarrolla para ejecución local. Las dependencias entre tareas están en [PLANNING.md](PLANNING.md).

Estados: **Pendiente**, **En curso**, **Bloqueada** y **Completada**. Una tarea bloqueada debe indicar el motivo; una tarea completada debe haber cumplido sus criterios de aceptación.

| ID | Tarea | Estado | Criterios de aceptación |
| --- | --- | --- | --- |
| T01 | Examinar la fuente de víctimas | Pendiente | Documentar campos, unidad de medida, cobertura, calidad y condiciones de uso del CSV; identificar cómo interpretar fecha, cantidad y códigos geográficos. |
| T02 | Evaluar datos geográficos | Pendiente | Identificar geometrías utilizables de departamentos y municipios, sus condiciones de uso y cobertura; documentar cómo unirlas con los códigos de la fuente y cómo tratar diferencias. |
| T03 | Preparar el proyecto local | Pendiente | Definir dependencias de Python, DuckDB y Streamlit y un procedimiento reproducible para instalar y ejecutar el proyecto. |
| T04 | Cargar y validar el CSV | Pendiente | Leer el archivo suministrado manualmente; validar campos y valores necesarios; informar errores y registros excluidos sin ocultarlos. |
| T05 | Calcular el total y los agregados | Pendiente | Calcular el total de víctimas y los agregados por departamento y municipio; conservar el contexto temporal y comprobar los resultados con datos de prueba. |
| T06 | Preparar los datos para el mapa | Pendiente | Unir agregados y geometrías para ambos niveles; informar códigos sin correspondencia y evitar asignar ubicaciones inventadas. |
| T07 | Construir el tablero | Pendiente | Mostrar el total y un mapa por departamento y municipio, junto con la fuente, el periodo y las limitaciones relevantes. |
| T08 | Verificar el flujo del MVP | Pendiente | Probar el flujo local, incluida la carga, los cálculos, las correspondencias geográficas y el manejo de errores, con casos representativos. |
| T09 | Documentar el uso local | Pendiente | Actualizar el README con instrucciones verificadas de instalación, descarga y ubicación del CSV, ejecución, actualización manual y limitaciones. |

## Decisiones pendientes

- Selección concreta de la fuente de geometrías y tratamiento de códigos sin correspondencia.
- Forma de interacción entre los niveles del mapa, según las posibilidades de los datos y la implementación.
