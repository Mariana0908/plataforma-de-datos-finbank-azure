# Modelo analitico Gold con Azure Databricks

Esta carpeta implementa la capa Gold de FinBank mediante PySpark, Delta Lake y
Unity Catalog. El resultado es un modelo dimensional gobernado y preparado para
consumo desde herramientas analiticas como Power BI.

## Componentes

- `src/01_silver_to_gold.py`: notebook fuente que construye dimensiones,
  hechos, marts y controles de conciliacion.
- `sql/validate_gold.sql`: consultas reproducibles para validar objetos,
  conteos, KPI, integridad, privacidad e idempotencia.

## Modelo publicado

### Dimensiones

| Tabla | Grano | Filas |
|---|---|---:|
| `dim_fecha` | Una fila por fecha del rango de negocio | 2.554 |
| `dim_cliente` | Una fila por cliente | 10.000 |
| `dim_producto` | Una fila por producto | 50 |
| `dim_sucursal` | Una fila por sucursal | 200 |

### Hechos

| Tabla | Grano | Filas |
|---|---|---:|
| `fact_movimientos` | Un movimiento financiero valido | 497.500 |
| `fact_obligaciones` | Una obligacion financiera | 30.000 |
| `fact_comisiones` | Un cobro de comision | 80.000 |

### Marts

| Tabla | Proposito | Filas |
|---|---|---:|
| `mart_cliente_360` | Vision consolidada de actividad, cartera y riesgo por cliente | 10.000 |
| `mart_producto_rendimiento` | Uso, cartera, mora e ingresos por producto | 50 |
| `kpi_resumen_bancario` | Indicadores ejecutivos a la fecha de corte | 1 |

## Transformaciones

- exclusión de movimientos fuera del periodo oficial;
- relaciones con dimensiones de cliente, producto y fecha;
- clasificacion de obligaciones por rango de mora;
- agregaciones financieras por cliente y producto;
- segmentacion de alerta de clientes en `ALTO`, `MEDIO` y `BAJO`;
- conciliacion de conteos y valores monetarios contra Silver;
- escritura idempotente de tablas Delta administradas.

## Indicadores principales

| Indicador | Resultado |
|---|---:|
| Clientes | 10.000 |
| Clientes activos | 9.092 |
| Movimientos validos | 497.500 |
| Movimientos sospechosos | 55.326 |
| Porcentaje sospechoso | 11,12 % |
| Obligaciones | 30.000 |
| Obligaciones en mora | 8.960 |
| Porcentaje en mora | 29,87 % |
| Saldo total de cartera | 73.708.263.853,29 |
| Ingreso total por comisiones | 1.206.647.607,37 |

El indicador sospechoso representa una señal estadistica para revision y no una
confirmacion de fraude.

## Privacidad y seguridad

Gold aplica minimizacion de datos: no publica nombres, apellidos, documentos,
fecha de nacimiento ni numeros de cuenta en texto claro. El numero de cuenta se
representa mediante un hash SHA-256. El acceso a ADLS Gen2 utiliza identidad
administrada y Unity Catalog.

## Ejecucion

1. Importar `src/01_silver_to_gold.py` como notebook fuente de Databricks.
2. Conectarlo a computo Serverless.
3. Confirmar los parametros `catalog` y `analysis_end_date`.
4. Ejecutar todas las celdas.
5. Ejecutar por bloques `sql/validate_gold.sql` en Databricks SQL.

Las tablas de negocio se escriben en modo `overwrite`, mientras que
`gold_run_metrics` conserva una entrada por objeto y ejecucion. Dos ejecuciones
consecutivas produjeron los mismos conteos.

## Documentacion relacionada

- [Modelo dimensional Gold](../../docs/modelo-dimensional-gold.md)
- [Evidencias Gold](../../docs/evidencias/pipelines/gold/README.md)
