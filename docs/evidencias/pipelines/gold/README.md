# Evidencias del modelo analitico Gold

Esta carpeta contiene evidencias de la construccion, validacion y uso del modelo
dimensional Gold de FinBank en Azure Databricks.
| N.º | Archivo | Evidencia |
|---:|---|---|
| 01 | [Procesamiento Silver–Gold exitoso](./01-procesamiento-silver-gold-exitoso.png) | Ejecución del notebook, diez objetos analíticos publicados y conciliaciones exitosas. |
| 02 | [Objetos Gold en Unity Catalog](./02-objetos-gold-unity-catalog.png) | Once tablas persistentes registradas en Unity Catalog, incluyendo la tabla técnica de métricas. |
| 03 | [KPI bancarios Gold](./03-kpis-bancarios-gold.png) | Indicadores ejecutivos consolidados a la fecha de corte. |
| 04 | [Integridad del modelo dimensional](./04-integridad-modelo-dimensional-gold.png) | Diez controles de integridad referencial con cero inconsistencias. |
| 05 | [Minimización de datos personales](./05-minimizacion-datos-personales-gold.png) | Ausencia de datos personales directos y protección del número de cuenta. |
| 06 | [Segmentación y alertas de clientes](./06-segmentacion-alerta-clientes-gold.png) | Distribución de clientes, movimientos, cartera y riesgo por nivel de alerta. |
| 07 | [Rendimiento de productos](./07-rendimiento-productos-gold.png) | Productos con mayor saldo de cartera y sus principales métricas de negocio. |
| 08 | [Idempotencia del modelo Gold](./08-idempotencia-modelo-gold.png) | Comparación estable de dos ejecuciones consecutivas del procesamiento. |
| 09 | [Validación consolidada Gold](./09-validacion-consolidada-gold.png) | Ejecución completa de los nueve bloques de validación e idempotencia confirmada para los diez objetos analíticos. |


## Resultado consolidado

- Cuatro dimensiones, tres tablas de hechos y tres objetos analíticos.
- 497.500 movimientos válidos disponibles para analítica.
- Cero relaciones huérfanas en el modelo dimensional.
- Cero columnas personales directas expuestas.
- Conciliaciones de conteos y valores financieros exitosas.
- Dos ejecuciones consecutivas con resultados idempotentes.
- Nueve bloques de validación ejecutados correctamente.

Las capturas excluyen credenciales, tokens e identificadores sensibles.
