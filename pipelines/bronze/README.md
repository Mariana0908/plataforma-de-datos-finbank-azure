# Ingesta incremental hacia Bronze

Esta carpeta contiene la implementación de la ingesta desde Azure SQL Database hacia la capa Bronze de Azure Data Lake Storage Gen2.

La solución utiliza Azure Data Factory y está diseñada como una canalización parametrizada y dirigida por metadatos, de modo que las seis tablas fuente pueden procesarse con una única canalización reutilizable.

## Flujo de la solución

1. Azure Data Factory consulta las configuraciones activas de ingesta.
2. Un `ForEach` procesa secuencialmente cada tabla configurada.
3. Se obtiene dinámicamente el comando de extracción correspondiente.
4. Se registra el inicio de la ejecución en las tablas de control.
5. Los datos se copian desde Azure SQL Database hacia ADLS Gen2 en formato Parquet.
6. Se registran las métricas de la ejecución y se actualiza el punto de control incremental.
7. Si ocurre un error, se registra el detalle y la actividad finaliza explícitamente como fallida.

## Tablas procesadas

| Tabla                | Estrategia incremental | Columna de control |
| -------------------- | ---------------------- | ------------------ |
| `TB_CLIENTES_CORE`   | Change Tracking        | `id_cli`           |
| `TB_PRODUCTOS_CAT`   | Change Tracking        | `cod_prod`         |
| `TB_OBLIGACIONES`    | Change Tracking        | `id_oblig`         |
| `TB_SUCURSALES_RED`  | Change Tracking        | `cod_suc`          |
| `TB_COMISIONES_LOG`  | Change Tracking        | `id_comision`      |
| `TB_MOV_FINANCIEROS` | Watermark incremental  | `id_mov`           |

`TB_MOV_FINANCIEROS` utiliza una marca de agua basada en `id_mov` porque representa una tabla transaccional de comportamiento principalmente append-only. Las demás tablas utilizan Change Tracking para identificar inserciones y actualizaciones.

## Componentes de Azure Data Factory

### Servicios vinculados

* `ls_akv_finbank_dev`: conexión con Azure Key Vault.
* `ls_azuresql_finbank_dev`: conexión con Azure SQL Database.
* `ls_adls_finbank_dev`: conexión con Azure Data Lake Storage Gen2.

Las credenciales de Azure SQL se recuperan desde Azure Key Vault y el acceso al Data Lake utiliza la identidad administrada de Azure Data Factory.

### Conjuntos de datos

* `ds_azuresql_dynamic`: conjunto de datos parametrizado para consultar cualquier tabla de Azure SQL.
* `ds_adls_bronze_parquet`: conjunto de datos parametrizado para escribir archivos Parquet en Bronze.

### Canalización

La canalización `pl_bronze_ingestion` contiene las siguientes actividades principales:

* `lkp_ingestion_config`
* `fe_ingest_tables`
* `lkp_extract_command`
* `sp_start_ingestion_run`
* `cpy_sql_to_bronze`
* `sp_complete_ingestion_run`
* `sp_fail_ingestion_run`
* `fail_bronze_copy`

## Organización de Bronze

Los archivos se almacenan con la siguiente estructura:

```text
bronze/
└── <tabla>/
    └── year=YYYY/
        └── month=MM/
            └── day=DD/
                └── <tabla>_<pipeline-run-id>.parquet
```

Los nombres de las tablas se normalizan a minúsculas en ADLS Gen2.

Cada archivo incorpora las siguientes columnas técnicas:

* `_ingestion_timestamp_utc`
* `_source_system`
* `_batch_id`

Estas columnas permiten identificar cuándo se produjo la ingesta, cuál fue el sistema de origen y qué ejecución generó cada registro.

## Control y observabilidad

Los scripts SQL de control están disponibles en:

* [`setup_bronze_control.sql`](./sql/setup_bronze_control.sql)
* [`bronze_control_procedures.sql`](./sql/bronze_control_procedures.sql)

La implementación registra:

* identificador de ejecución;
* identificador de lote;
* tabla procesada;
* fecha y hora de inicio y finalización;
* estado de la ejecución;
* filas leídas y copiadas;
* bytes escritos;
* duración;
* ruta de salida;
* mensaje y detalle del error;
* versión de Change Tracking o watermark procesado.

## Resultados de las pruebas

### Carga inicial

La primera ejecución procesó correctamente las seis tablas:

| Tabla                | Filas copiadas |
| -------------------- | -------------: |
| `TB_CLIENTES_CORE`   |         10.000 |
| `TB_PRODUCTOS_CAT`   |             50 |
| `TB_MOV_FINANCIEROS` |        500.000 |
| `TB_OBLIGACIONES`    |         30.000 |
| `TB_SUCURSALES_RED`  |            200 |
| `TB_COMISIONES_LOG`  |         80.000 |
| **Total**            |    **620.250** |

La ejecución inicial escribió 28.689.617 bytes y todas las tablas finalizaron con estado `SUCCEEDED`.

### Prueba incremental controlada

Para verificar la incrementalidad se realizaron dos cambios controlados:

* modificación de un cliente;
* inserción de un movimiento con `id_mov = 900000001`.

La siguiente ejecución procesó únicamente:

* 1 registro de `TB_CLIENTES_CORE`;
* 1 registro de `TB_MOV_FINANCIEROS`;
* 0 registros nuevos en las otras cuatro tablas.

El resultado confirma que la canalización no volvió a extraer los 620.250 registros de la carga inicial.

Cuando una tabla no presenta cambios, Azure Data Factory puede generar un archivo Parquet sin filas para conservar la ejecución parametrizada. El log registra correctamente cero filas leídas y copiadas.

## Plantillas de Azure Data Factory

Las plantillas ARM exportadas desde Azure Data Factory se encuentran en:

[`adf/arm-template`](./adf/arm-template/)

Estas plantillas permiten conservar y reproducir los servicios vinculados, conjuntos de datos y la canalización desarrollada.

Los valores sensibles no se almacenan de manera literal en las plantillas.

## Evidencias

Las evidencias de configuración, ejecución, almacenamiento y validación incremental están disponibles en:

[Evidencias de la ingesta Bronze](../../docs/evidencias/pipelines/bronze/README.md)
