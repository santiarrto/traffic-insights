# Planificación y dependencias de tareas

Una tarea puede iniciarse cuando sus dependencias directas estén completadas. Los roles, estados y criterios están en [TASKS.md](TASKS.md); las dependencias transitivas se cumplen a través de sus prerrequisitos.

| Tarea | Depende de |
| --- | --- |
| T01 | Ninguna |
| T02 | T01 |
| T03 | Ninguna |
| T04 | T01, T03 |
| T05 | T04 |
| T06 | T02, T05 |
| T07 | T06 |
| T08 | T07 |
| T09 | T08 |
| T10 | T09 |

T01 y T03 pueden comenzar en paralelo. T02 y T04 pueden avanzar en paralelo una vez cumplidos sus respectivos prerrequisitos. Las pruebas de cada componente se realizan durante su implementación; T08 verifica el flujo completo. T10 amplía el tablero después del MVP.
