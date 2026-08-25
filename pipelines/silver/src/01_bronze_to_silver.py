# Databricks notebook source
# MAGIC %md
# MAGIC # FinBank - Transformacion Bronze a Silver
# MAGIC
# MAGIC Procesamiento idempotente de las seis tablas fuente. Consolida los
# MAGIC archivos iniciales e incrementales, conserva la trazabilidad tecnica,
# MAGIC registra anomalías en cuarentena y publica tablas Delta en Unity Catalog.

# COMMAND ----------

from datetime import datetime, timezone
from functools import reduce
from typing import Dict, List, Tuple
from uuid import uuid4

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import StringType


spark.conf.set("spark.sql.session.timeZone", "UTC")

dbutils.widgets.text("catalog", "dbw_finbank_dev_eus", "Catalogo de Unity Catalog")
dbutils.widgets.text("start_date", "2025-08-01", "Fecha inicial valida")
dbutils.widgets.text("end_date", "2026-08-24", "Fecha final valida")

CATALOG = dbutils.widgets.get("catalog")
START_DATE = dbutils.widgets.get("start_date")
END_DATE = dbutils.widgets.get("end_date")

BRONZE_ROOT = f"/Volumes/{CATALOG}/bronze/raw_files"
SILVER_SCHEMA = f"{CATALOG}.silver"
QUALITY_SCHEMA = f"{CATALOG}.quality"
RUN_ID = str(uuid4())
PROCESSED_AT_UTC = datetime.now(timezone.utc)

ALLOWED_CHANNELS = [
    "APP",
    "WEB",
    "ATM",
    "PSE",
    "ACH",
    "CORRESPONSAL",
    "SUCURSAL",
]

TABLE_CONFIG: Dict[str, Dict[str, object]] = {
    "tb_clientes_core": {
        "primary_key": "id_cli",
        "uppercase": ["tip_doc", "cod_segmento", "estado_cli", "canal_adquis"],
    },
    "tb_productos_cat": {
        "primary_key": "cod_prod",
        "uppercase": ["cod_prod", "tip_prod", "estado_prod"],
    },
    "tb_sucursales_red": {
        "primary_key": "cod_suc",
        "uppercase": ["cod_suc", "tip_punto"],
    },
    "tb_obligaciones": {
        "primary_key": "id_oblig",
        "uppercase": ["cod_prod", "calif_riesgo"],
    },
    "tb_comisiones_log": {
        "primary_key": "id_comision",
        "uppercase": ["cod_prod", "tip_comision", "estado_cobro"],
    },
    "tb_mov_financieros": {
        "primary_key": "id_mov",
        "uppercase": ["cod_prod", "tip_mov", "cod_canal", "cod_estado_mov"],
    },
}

quarantine_frames: List[DataFrame] = []
run_metrics: List[Dict[str, object]] = []


# COMMAND ----------

def read_bronze(table_name: str) -> DataFrame:
    """Lee todas las particiones Parquet de una tabla Bronze."""
    table_path = f"{BRONZE_ROOT}/{table_name}"
    return (
        spark.read.format("parquet")
        .option("recursiveFileLookup", "true")
        .load(table_path)
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn(
            "_ingestion_timestamp_utc",
            F.to_timestamp(F.col("_ingestion_timestamp_utc")),
        )
    )


def standardize_strings(df: DataFrame, uppercase_columns: List[str]) -> DataFrame:
    """Elimina espacios laterales y normaliza campos de catalogo."""
    result = df
    for field in result.schema.fields:
        if isinstance(field.dataType, StringType):
            result = result.withColumn(field.name, F.trim(F.col(field.name)))

    for column_name in uppercase_columns:
        if column_name in result.columns:
            result = result.withColumn(column_name, F.upper(F.col(column_name)))

    return result


def quarantine_projection(
    df: DataFrame,
    table_name: str,
    primary_key: str,
    quality_rules_column: str = "_quality_rules",
) -> DataFrame:
    """Convierte cualquier esquema fuente al esquema comun de cuarentena."""
    record_columns = [
        F.col(column_name)
        for column_name in df.columns
        if column_name != quality_rules_column
    ]

    batch_column = (
        F.col("_batch_id").cast("string")
        if "_batch_id" in df.columns
        else F.lit(None).cast("string")
    )
    ingestion_column = (
        F.col("_ingestion_timestamp_utc").cast("timestamp")
        if "_ingestion_timestamp_utc" in df.columns
        else F.lit(None).cast("timestamp")
    )
    source_file_column = (
        F.col("_source_file").cast("string")
        if "_source_file" in df.columns
        else F.lit(None).cast("string")
    )

    return df.select(
        F.lit(RUN_ID).alias("run_id"),
        F.lit(table_name).alias("table_name"),
        F.col(primary_key).cast("string").alias("primary_key_value"),
        F.col(quality_rules_column).cast("string").alias("quality_rules"),
        F.to_json(F.struct(*record_columns)).alias("record_json"),
        batch_column.alias("batch_id"),
        ingestion_column.alias("ingestion_timestamp_utc"),
        source_file_column.alias("source_file"),
        F.current_timestamp().alias("quarantined_at_utc"),
    )


def add_to_quarantine(
    df: DataFrame,
    table_name: str,
    primary_key: str,
    quality_rules_column: str = "_quality_rules",
) -> None:
    quarantine_frames.append(
        quarantine_projection(
            df,
            table_name,
            primary_key,
            quality_rules_column,
        )
    )


def deduplicate_latest(
    df: DataFrame,
    table_name: str,
    primary_key: str,
) -> DataFrame:
    """Conserva la version mas reciente de cada llave y audita descartes."""
    null_keys = df.filter(F.col(primary_key).isNull()).withColumn(
        "_quality_rules", F.lit("LLAVE_PRIMARIA_NULA")
    )
    add_to_quarantine(null_keys, table_name, primary_key)

    ranking_window = Window.partitionBy(primary_key).orderBy(
        F.col("_ingestion_timestamp_utc").desc_nulls_last(),
        F.col("_source_file").desc_nulls_last(),
    )

    ranked = (
        df.filter(F.col(primary_key).isNotNull())
        .withColumn("_duplicate_rank", F.row_number().over(ranking_window))
    )

    duplicate_copies = (
        ranked.filter(F.col("_duplicate_rank") > 1)
        .drop("_duplicate_rank")
        .withColumn("_quality_rules", F.lit("REGISTRO_DUPLICADO_DESCARTADO"))
    )
    add_to_quarantine(duplicate_copies, table_name, primary_key)

    return ranked.filter(F.col("_duplicate_rank") == 1).drop("_duplicate_rank")


def prepare_table(table_name: str) -> Tuple[DataFrame, int]:
    config = TABLE_CONFIG[table_name]
    raw_df = read_bronze(table_name)
    raw_count = raw_df.count()
    standardized = standardize_strings(raw_df, config["uppercase"])
    canonical = deduplicate_latest(
        standardized,
        table_name,
        config["primary_key"],
    )
    return canonical, raw_count


def add_record_hash(df: DataFrame) -> DataFrame:
    """Agrega hash de negocio y fecha tecnica del procesamiento Silver."""
    excluded_columns = {
        "_source_file",
        "_ingestion_timestamp_utc",
        "_source_system",
        "_batch_id",
        "_silver_processed_at_utc",
        "_record_hash",
    }
    business_columns = sorted(
        column_name
        for column_name in df.columns
        if column_name not in excluded_columns
    )
    hash_expression = F.concat_ws(
        "||",
        *[
            F.coalesce(F.col(column_name).cast("string"), F.lit("<NULL>"))
            for column_name in business_columns
        ],
    )
    return (
        df.withColumn("_record_hash", F.sha2(hash_expression, 256))
        .withColumn("_silver_processed_at_utc", F.current_timestamp())
    )


def write_silver(df: DataFrame, table_name: str) -> int:
    """Publica una fotografia idempotente como tabla Delta administrada."""
    target_table = f"{SILVER_SCHEMA}.{table_name}"
    prepared = add_record_hash(df)
    row_count = prepared.count()
    (
        prepared.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target_table)
    )
    return row_count


def register_metric(table_name: str, bronze_rows: int, silver_rows: int) -> None:
    run_metrics.append(
        {
            "run_id": RUN_ID,
            "table_name": table_name,
            "bronze_rows": int(bronze_rows),
            "silver_rows": int(silver_rows),
            "processed_at_utc": PROCESSED_AT_UTC,
        }
    )


def add_reference_rules(
    df: DataFrame,
    table_name: str,
    primary_key: str,
    valid_clients: DataFrame,
    valid_products: DataFrame,
) -> DataFrame:
    """Valida las relaciones de cliente y producto y excluye huerfanos."""
    with_references = (
        df.join(F.broadcast(valid_clients), on="id_cli", how="left")
        .join(F.broadcast(valid_products), on="cod_prod", how="left")
        .withColumn(
            "_quality_rules",
            F.concat_ws(
                "|",
                F.when(
                    ~F.coalesce(F.col("_client_exists"), F.lit(False)),
                    F.lit("CLIENTE_INEXISTENTE"),
                ),
                F.when(
                    ~F.coalesce(F.col("_product_exists"), F.lit(False)),
                    F.lit("PRODUCTO_INEXISTENTE"),
                ),
            ),
        )
    )

    invalid_references = with_references.filter(
        (F.length(F.col("_quality_rules")) > 0)
    )
    add_to_quarantine(invalid_references, table_name, primary_key)

    return (
        with_references.filter(F.length(F.col("_quality_rules")) == 0)
        .drop("_quality_rules", "_client_exists", "_product_exists")
    )


# COMMAND ----------
# MAGIC %md
# MAGIC ## Dimensiones y catalogos

# COMMAND ----------

clientes, clientes_bronze_rows = prepare_table("tb_clientes_core")
productos, productos_bronze_rows = prepare_table("tb_productos_cat")
sucursales, sucursales_bronze_rows = prepare_table("tb_sucursales_red")

clientes_silver_rows = write_silver(clientes, "tb_clientes_core")
productos_silver_rows = write_silver(productos, "tb_productos_cat")
sucursales_silver_rows = write_silver(sucursales, "tb_sucursales_red")

register_metric("tb_clientes_core", clientes_bronze_rows, clientes_silver_rows)
register_metric("tb_productos_cat", productos_bronze_rows, productos_silver_rows)
register_metric("tb_sucursales_red", sucursales_bronze_rows, sucursales_silver_rows)

valid_clients = clientes.select("id_cli").distinct().withColumn(
    "_client_exists", F.lit(True)
)
valid_products = productos.select("cod_prod").distinct().withColumn(
    "_product_exists", F.lit(True)
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Obligaciones y comisiones

# COMMAND ----------

obligaciones, obligaciones_bronze_rows = prepare_table("tb_obligaciones")
obligaciones = add_reference_rules(
    obligaciones,
    "tb_obligaciones",
    "id_oblig",
    valid_clients,
    valid_products,
).withColumn(
    "ind_montos_consistentes",
    (F.col("vr_aprobado") >= F.col("vr_desembolsado"))
    & (F.col("vr_desembolsado") >= F.col("sdo_capital"))
    & (F.col("sdo_capital") >= 0),
).withColumn(
    "ind_fechas_consistentes",
    F.col("fec_venc") > F.col("fec_desembolso"),
)

invalid_obligations = obligaciones.filter(
    (~F.col("ind_montos_consistentes")) | (~F.col("ind_fechas_consistentes"))
).withColumn(
    "_quality_rules",
    F.concat_ws(
        "|",
        F.when(
            ~F.col("ind_montos_consistentes"),
            F.lit("MONTOS_OBLIGACION_INCONSISTENTES"),
        ),
        F.when(
            ~F.col("ind_fechas_consistentes"),
            F.lit("FECHAS_OBLIGACION_INCONSISTENTES"),
        ),
    ),
)
add_to_quarantine(
    invalid_obligations,
    "tb_obligaciones",
    "id_oblig",
)

obligaciones_silver_rows = write_silver(obligaciones, "tb_obligaciones")
register_metric(
    "tb_obligaciones",
    obligaciones_bronze_rows,
    obligaciones_silver_rows,
)

comisiones, comisiones_bronze_rows = prepare_table("tb_comisiones_log")
comisiones = add_reference_rules(
    comisiones,
    "tb_comisiones_log",
    "id_comision",
    valid_clients,
    valid_products,
)

invalid_commissions = comisiones.filter(F.col("vr_comision") < 0).withColumn(
    "_quality_rules", F.lit("VALOR_COMISION_NEGATIVO")
)
add_to_quarantine(
    invalid_commissions,
    "tb_comisiones_log",
    "id_comision",
)

comisiones_silver_rows = write_silver(comisiones, "tb_comisiones_log")
register_metric(
    "tb_comisiones_log",
    comisiones_bronze_rows,
    comisiones_silver_rows,
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Movimientos financieros

# COMMAND ----------

movimientos, movimientos_bronze_rows = prepare_table("tb_mov_financieros")
movimientos = add_reference_rules(
    movimientos,
    "tb_mov_financieros",
    "id_mov",
    valid_clients,
    valid_products,
)

movimientos = (
    movimientos.withColumn("cod_canal_original", F.col("cod_canal"))
    .withColumn(
        "ind_fecha_rango_valido",
        F.col("fec_mov").between(
            F.to_date(F.lit(START_DATE)),
            F.to_date(F.lit(END_DATE)),
        ),
    )
    .withColumn(
        "ind_canal_valido",
        F.col("cod_canal_original").isin(ALLOWED_CHANNELS),
    )
    .withColumn(
        "_quality_rules",
        F.concat_ws(
            "|",
            F.when(
                ~F.col("ind_fecha_rango_valido"),
                F.lit("FECHA_MOVIMIENTO_FUERA_RANGO"),
            ),
            F.when(
                ~F.col("ind_canal_valido"),
                F.lit("CANAL_TRANSACCIONAL_INVALIDO"),
            ),
        ),
    )
)

invalid_movements = movimientos.filter(
    F.length(F.col("_quality_rules")) > 0
)
add_to_quarantine(
    invalid_movements,
    "tb_mov_financieros",
    "id_mov",
)

movimientos = movimientos.withColumn(
    "cod_canal",
    F.when(F.col("ind_canal_valido"), F.col("cod_canal_original")).otherwise(
        F.lit("DESCONOCIDO")
    ),
).drop("_quality_rules")

# El indicador usa solamente movimientos dentro del periodo oficial.
movimientos_validos_estadistica = (
    movimientos.filter(F.col("ind_fecha_rango_valido"))
    .withColumn("_event_seconds", F.col("fec_mov").cast("timestamp").cast("long"))
)

rolling_window = (
    Window.partitionBy("id_cli")
    .orderBy(F.col("_event_seconds"))
    .rangeBetween(-(30 * 24 * 60 * 60), -1)
)

rolling_statistics = movimientos_validos_estadistica.select(
    "id_mov",
    F.avg("vr_mov").over(rolling_window).alias("promedio_vr_mov_30d"),
    F.stddev_samp("vr_mov").over(rolling_window).alias("desv_vr_mov_30d"),
    F.count("vr_mov").over(rolling_window).alias("cantidad_mov_30d"),
)

movimientos = (
    movimientos.join(rolling_statistics, on="id_mov", how="left")
    .withColumn(
        "ind_sospechoso",
        F.when(
            F.col("ind_fecha_rango_valido")
            & (F.col("cantidad_mov_30d") >= 2)
            & (
                F.col("vr_mov")
                > (
                    F.col("promedio_vr_mov_30d")
                    + 3 * F.coalesce(F.col("desv_vr_mov_30d"), F.lit(0))
                )
            ),
            F.lit(True),
        ).otherwise(F.lit(False)),
    )
    .withColumn("promedio_vr_mov_30d", F.round("promedio_vr_mov_30d", 2))
    .withColumn("desv_vr_mov_30d", F.round("desv_vr_mov_30d", 2))
)

movimientos_silver_rows = write_silver(movimientos, "tb_mov_financieros")
register_metric(
    "tb_mov_financieros",
    movimientos_bronze_rows,
    movimientos_silver_rows,
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Publicacion de cuarentena y metricas

# COMMAND ----------

quarantine_df = reduce(
    lambda left, right: left.unionByName(right, allowMissingColumns=True),
    quarantine_frames,
)

(
    quarantine_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{QUALITY_SCHEMA}.rejected_records")
)

quality_summary = (
    quarantine_df.withColumn(
        "quality_rule",
        F.explode(F.split(F.col("quality_rules"), r"\|")),
    )
    .groupBy("table_name", "quality_rule")
    .agg(F.count(F.lit(1)).alias("rejected_rows"))
    .withColumn("run_id", F.lit(RUN_ID))
    .withColumn("processed_at_utc", F.current_timestamp())
)

(
    quality_summary.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{QUALITY_SCHEMA}.rule_summary")
)

quarantine_counts = {
    row["table_name"]: int(row["quarantined_rows"])
    for row in quarantine_df.groupBy("table_name")
    .agg(F.count(F.lit(1)).alias("quarantined_rows"))
    .collect()
}

metrics_rows = [
    {
        **metric,
        "quarantined_rows": quarantine_counts.get(metric["table_name"], 0),
    }
    for metric in run_metrics
]
metrics_df = spark.createDataFrame(metrics_rows).select(
    "run_id",
    "table_name",
    "bronze_rows",
    "silver_rows",
    "quarantined_rows",
    "processed_at_utc",
)

if metrics_df.count() != len(TABLE_CONFIG):
    raise RuntimeError("No se generaron metricas para las seis tablas fuente.")

if metrics_df.filter(F.col("silver_rows") <= 0).limit(1).count() > 0:
    raise RuntimeError("Una o mas tablas Silver quedaron sin registros.")

if (
    movimientos.filter(~F.col("cod_canal").isin(ALLOWED_CHANNELS + ["DESCONOCIDO"]))
    .limit(1)
    .count()
    > 0
):
    raise RuntimeError("Silver contiene canales transaccionales no estandarizados.")

(
    metrics_df.write.format("delta")
    .mode("append")
    .saveAsTable(f"{QUALITY_SCHEMA}.silver_run_metrics")
)

print(f"SILVER_RUN_ID: {RUN_ID}")
print("PROCESAMIENTO BRONZE -> SILVER: SUCCESS")
display(metrics_df.orderBy("table_name"))
display(quality_summary.orderBy("table_name", "quality_rule"))