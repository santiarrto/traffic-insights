# Planificación y dependencias de tareas

Una tarea puede iniciarse cuando todas las tareas indicadas en **Depende de** estén completadas. Los identificadores y estados se mantienen en [TASKS.md](TASKS.md).

| Tarea | Depende de | Motivo |
| --- | --- | --- |
| T01 | Ninguna | La fuente de víctimas puede examinarse de forma independiente. |
| T02 | T01 | La evaluación geográfica necesita conocer los códigos y la cobertura de la fuente de víctimas. |
| T03 | Ninguna | La preparación del proyecto puede comenzar de forma independiente. |
| T04 | T01, T03 | La carga necesita el esquema conocido y el entorno de ejecución. |
| T05 | T04 | Los indicadores necesitan datos cargados y validados. |
| T06 | T02, T05 | El mapa necesita geometrías evaluadas y datos agregados. |
| T07 | T03, T05, T06 | El tablero necesita el entorno, el indicador y los datos del mapa. |
| T08 | T04, T05, T06, T07 | La verificación cubre el flujo implementado de extremo a extremo. |
| T09 | T01, T02, T03, T07, T08 | La documentación debe reflejar las fuentes, la instalación y el flujo verificado. |
