# Procesamiento Silver con Azure Databricks

Esta carpeta implementa la transformación de los archivos Parquet de Bronze en
tablas Delta gobernadas mediante Unity Catalog.

## Componentes

- `sql/setup_unity_catalog.sql`: crea los esquemas y volúmenes externos de la
  arquitectura Medallion.
- `sql/validate_silver.sql`: contiene validaciones reproducibles de conteos,
  calidad, integridad referencial e idempotencia.
- `src/01_bronze_to_silver.py`: notebook fuente de Databricks para procesar las
  seis tablas de FinBank.

## Flujo

1. Lee todas las particiones Parquet de cada tabla desde el volumen Bronze.
2. Consolida la carga inicial y las ejecuciones incrementales.
3. Normaliza campos de texto y valores de catálogo.
4. Deduplica por llave primaria conservando la versión más reciente.
5. Valida relaciones con clientes y productos.
6. Detecta anomalías y registra las filas en `quality.rejected_records`.
7. Calcula el indicador de movimiento sospechoso con una ventana histórica de
   30 días por cliente.
8. Publica tablas Delta administradas en el esquema `silver`.
9. Registra métricas por ejecución en `quality.silver_run_metrics`.

## Tablas publicadas

| Tabla Silver | Filas |
|---|---:|
| `tb_clientes_core` | 10.000 |
| `tb_productos_cat` | 50 |
| `tb_sucursales_red` | 200 |
| `tb_obligaciones` | 30.000 |
| `tb_comisiones_log` | 80.000 |
| `tb_mov_financieros` | 498.501 |

## Reglas de calidad verificadas

- descarte auditable de duplicados;
- fechas transaccionales fuera del periodo oficial;
- canales inválidos mapeados a `DESCONOCIDO`;
- validación de llaves foráneas;
- consistencia de montos y fechas de obligaciones;
- valores negativos de comisiones;
- trazabilidad mediante archivo fuente, lote, fecha de ingesta y hash SHA-256.

Las anomalías permanecen disponibles en el esquema `quality` y no se eliminan
de forma silenciosa.

## Indicador de movimientos sospechosos

Un movimiento se marca con `ind_sospechoso = true` cuando su valor supera el
promedio más tres desviaciones estándar del mismo cliente durante los 30 días
anteriores. El resultado es un indicador para revisión y no una confirmación de
fraude.

## Ejecución

1. Importar `src/01_bronze_to_silver.py` como notebook fuente de Databricks.
2. Conectarlo a cómputo Serverless.
3. Confirmar los parámetros `catalog`, `start_date` y `end_date`.
4. Ejecutar todas las celdas.
5. Ejecutar los bloques de `sql/validate_silver.sql` en Databricks SQL.

El proceso utiliza escrituras `overwrite` para las tablas de negocio, por lo
que puede repetirse sin duplicar información. Cada ejecución conserva métricas
con un `run_id` independiente.

## Seguridad

Databricks accede a ADLS Gen2 mediante una identidad administrada y una
credencial de almacenamiento de Unity Catalog. El código no contiene claves,
tokens SAS ni cadenas de conexión.

## Evidencias

Las evidencias de configuración, ejecución y validación están documentadas en
[`docs/evidencias/pipelines/silver`](../../docs/evidencias/pipelines/silver/README.md).
