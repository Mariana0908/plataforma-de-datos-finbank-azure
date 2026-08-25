# Databricks notebook source
# MAGIC %md
# MAGIC # FinBank - Modelo analitico Gold
# MAGIC
# MAGIC Construye dimensiones, hechos y marts bancarios a partir de las tablas
# MAGIC Delta Silver. El proceso es idempotente, minimiza datos personales y
# MAGIC valida conteos, unicidad, integridad referencial y totales financieros.

# COMMAND ----------

from datetime import datetime, timezone
from functools import reduce
from typing import Dict, List, Sequence
from uuid import uuid4

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


spark.conf.set("spark.sql.session.timeZone", "UTC")

dbutils.widgets.text("catalog", "dbw_finbank_dev_eus", "Catalogo de Unity Catalog")
dbutils.widgets.text("analysis_end_date", "2026-08-24", "Fecha de corte analitica")

CATALOG = dbutils.widgets.get("catalog")
ANALYSIS_END_DATE = dbutils.widgets.get("analysis_end_date")
SILVER_SCHEMA = f"{CATALOG}.silver"
GOLD_SCHEMA = f"{CATALOG}.gold"
RUN_ID = str(uuid4())
PROCESSED_AT_UTC = datetime.now(timezone.utc)

SOURCE_TABLES = [
    "tb_clientes_core",
    "tb_productos_cat",
    "tb_sucursales_red",
    "tb_mov_financieros",
    "tb_obligaciones",
    "tb_comisiones_log",
]

gold_metrics: List[Dict[str, object]] = []


# COMMAND ----------

def require_silver_tables() -> None:
    missing = [
        table_name
        for table_name in SOURCE_TABLES
        if not spark.catalog.tableExists(f"{SILVER_SCHEMA}.{table_name}")
    ]
    if missing:
        raise RuntimeError(
            "No existen todas las fuentes Silver requeridas: " + ", ".join(missing)
        )


def assert_unique(df: DataFrame, key_columns: Sequence[str], table_name: str) -> None:
    duplicate_exists = (
        df.groupBy(*key_columns)
        .count()
        .filter(F.col("count") > 1)
        .limit(1)
        .count()
        > 0
    )
    if duplicate_exists:
        raise RuntimeError(
            f"La tabla Gold {table_name} contiene llaves duplicadas: {key_columns}"
        )


def publish_gold(
    df: DataFrame,
    table_name: str,
    key_columns: Sequence[str],
    table_type: str,
) -> int:
    if key_columns:
        assert_unique(df, key_columns, table_name)

    row_count = df.count()
    if row_count <= 0:
        raise RuntimeError(f"La tabla Gold {table_name} quedo vacia.")

    (
        df.withColumn("_gold_processed_at_utc", F.current_timestamp())
        .write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{GOLD_SCHEMA}.{table_name}")
    )

    gold_metrics.append(
        {
            "run_id": RUN_ID,
            "table_name": table_name,
            "table_type": table_type,
            "row_count": int(row_count),
            "processed_at_utc": PROCESSED_AT_UTC,
        }
    )
    return row_count


def assert_no_orphans(
    fact_df: DataFrame,
    dimension_df: DataFrame,
    fact_key: str,
    dimension_key: str,
    relation_name: str,
) -> None:
    orphan_exists = (
        fact_df.join(
            dimension_df.select(dimension_key),
            fact_df[fact_key] == dimension_df[dimension_key],
            "left_anti",
        )
        .limit(1)
        .count()
        > 0
    )
    if orphan_exists:
        raise RuntimeError(f"Se detectaron registros huerfanos en {relation_name}.")


def assert_decimal_equal(left_value, right_value, metric_name: str) -> None:
    if left_value != right_value:
        raise RuntimeError(
            f"La conciliacion {metric_name} fallo: Silver={left_value}, Gold={right_value}"
        )


require_silver_tables()

clientes = spark.table(f"{SILVER_SCHEMA}.tb_clientes_core")
productos = spark.table(f"{SILVER_SCHEMA}.tb_productos_cat")
sucursales = spark.table(f"{SILVER_SCHEMA}.tb_sucursales_red")
movimientos = spark.table(f"{SILVER_SCHEMA}.tb_mov_financieros")
obligaciones = spark.table(f"{SILVER_SCHEMA}.tb_obligaciones")
comisiones = spark.table(f"{SILVER_SCHEMA}.tb_comisiones_log")


# COMMAND ----------
# MAGIC %md
# MAGIC ## Dimensiones

# COMMAND ----------

# La dimension fecha cubre todas las fechas de negocio utilizadas por los hechos.
business_dates = reduce(
    lambda left, right: left.unionByName(right),
    [
        movimientos.filter(F.col("ind_fecha_rango_valido")).select(
            F.col("fec_mov").cast("date").alias("fecha")
        ),
        obligaciones.select(F.col("fec_desembolso").cast("date").alias("fecha")),
        obligaciones.select(F.col("fec_venc").cast("date").alias("fecha")),
        comisiones.select(F.col("fec_cobro").cast("date").alias("fecha")),
    ],
).filter(F.col("fecha").isNotNull())

date_bounds = business_dates.agg(
    F.min("fecha").alias("min_fecha"),
    F.max("fecha").alias("max_fecha"),
).first()

if date_bounds["min_fecha"] is None or date_bounds["max_fecha"] is None:
    raise RuntimeError("No fue posible determinar el rango de la dimension fecha.")

month_names = F.create_map(
    *sum(
        ([F.lit(month_number), F.lit(month_name)] for month_number, month_name in [
            (1, "ENERO"),
            (2, "FEBRERO"),
            (3, "MARZO"),
            (4, "ABRIL"),
            (5, "MAYO"),
            (6, "JUNIO"),
            (7, "JULIO"),
            (8, "AGOSTO"),
            (9, "SEPTIEMBRE"),
            (10, "OCTUBRE"),
            (11, "NOVIEMBRE"),
            (12, "DICIEMBRE"),
        ]),
        [],
    )
)

day_names = F.create_map(
    *sum(
        ([F.lit(day_number), F.lit(day_name)] for day_number, day_name in [
            (1, "DOMINGO"),
            (2, "LUNES"),
            (3, "MARTES"),
            (4, "MIERCOLES"),
            (5, "JUEVES"),
            (6, "VIERNES"),
            (7, "SABADO"),
        ]),
        [],
    )
)

dim_fecha = (
    spark.range(1)
    .select(
        F.explode(
            F.sequence(
                F.lit(date_bounds["min_fecha"]),
                F.lit(date_bounds["max_fecha"]),
                F.expr("INTERVAL 1 DAY"),
            )
        ).alias("fecha")
    )
    .select(
        F.date_format("fecha", "yyyyMMdd").cast("int").alias("fecha_key"),
        "fecha",
        F.year("fecha").alias("anio"),
        F.quarter("fecha").alias("trimestre"),
        F.month("fecha").alias("mes"),
        month_names[F.month("fecha")].alias("nombre_mes"),
        F.weekofyear("fecha").alias("semana_anio"),
        F.dayofmonth("fecha").alias("dia_mes"),
        F.dayofweek("fecha").alias("dia_semana"),
        day_names[F.dayofweek("fecha")].alias("nombre_dia"),
        F.dayofweek("fecha").isin([1, 7]).alias("es_fin_semana"),
    )
)

dim_cliente = (
    clientes.select(
        F.col("id_cli").alias("cliente_key"),
        "cod_segmento",
        "score_buro",
        "ciudad_res",
        "depto_res",
        "estado_cli",
        "canal_adquis",
        "fec_nac",
        "fec_alta",
        "_record_hash",
    )
    .withColumn(
        "edad_fecha_corte",
        F.floor(
            F.months_between(F.to_date(F.lit(ANALYSIS_END_DATE)), F.col("fec_nac"))
            / 12
        ).cast("int"),
    )
    .withColumn(
        "rango_edad",
        F.when(F.col("edad_fecha_corte") < 25, "18-24")
        .when(F.col("edad_fecha_corte") < 35, "25-34")
        .when(F.col("edad_fecha_corte") < 45, "35-44")
        .when(F.col("edad_fecha_corte") < 55, "45-54")
        .when(F.col("edad_fecha_corte") < 65, "55-64")
        .otherwise("65+"),
    )
    .withColumn(
        "rango_score_buro",
        F.when(F.col("score_buro").isNull(), "SIN_INFORMACION")
        .when(F.col("score_buro") < 500, "MUY_BAJO")
        .when(F.col("score_buro") < 650, "BAJO")
        .when(F.col("score_buro") < 750, "MEDIO")
        .otherwise("ALTO"),
    )
    .withColumn(
        "fecha_alta_key", F.date_format("fec_alta", "yyyyMMdd").cast("int")
    )
    .drop("fec_nac", "fec_alta")
)

dim_producto = productos.select(
    F.col("cod_prod").alias("producto_key"),
    "desc_prod",
    "tip_prod",
    "tasa_ea",
    "plazo_max_meses",
    "cuota_min",
    "comision_admin",
    "estado_prod",
    "_record_hash",
)

dim_sucursal = sucursales.select(
    F.col("cod_suc").alias("sucursal_key"),
    "nom_suc",
    "tip_punto",
    "ciudad",
    "depto",
    "latitud",
    "longitud",
    "activo",
    "_record_hash",
)

dim_fecha_rows = publish_gold(dim_fecha, "dim_fecha", ["fecha_key"], "DIMENSION")
dim_cliente_rows = publish_gold(
    dim_cliente, "dim_cliente", ["cliente_key"], "DIMENSION"
)
dim_producto_rows = publish_gold(
    dim_producto, "dim_producto", ["producto_key"], "DIMENSION"
)
dim_sucursal_rows = publish_gold(
    dim_sucursal, "dim_sucursal", ["sucursal_key"], "DIMENSION"
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Tablas de hechos

# COMMAND ----------

fact_movimientos = movimientos.filter(F.col("ind_fecha_rango_valido")).select(
    "id_mov",
    F.col("id_cli").alias("cliente_key"),
    F.col("cod_prod").alias("producto_key"),
    F.date_format("fec_mov", "yyyyMMdd").cast("int").alias("fecha_key"),
    "hra_mov",
    F.sha2(F.col("num_cuenta"), 256).alias("num_cuenta_hash"),
    "vr_mov",
    "tip_mov",
    "cod_canal",
    "cod_ciudad",
    "cod_estado_mov",
    "ind_canal_valido",
    "ind_sospechoso",
    "promedio_vr_mov_30d",
    "desv_vr_mov_30d",
    "cantidad_mov_30d",
    "_record_hash",
)

fact_obligaciones = (
    obligaciones.select(
        "id_oblig",
        F.col("id_cli").alias("cliente_key"),
        F.col("cod_prod").alias("producto_key"),
        "vr_aprobado",
        "vr_desembolsado",
        "sdo_capital",
        "vr_cuota",
        F.date_format("fec_desembolso", "yyyyMMdd")
        .cast("int")
        .alias("fecha_desembolso_key"),
        F.date_format("fec_venc", "yyyyMMdd").cast("int").alias("fecha_venc_key"),
        "dias_mora_act",
        "num_cuotas_pend",
        "calif_riesgo",
        "ind_montos_consistentes",
        "ind_fechas_consistentes",
        "_record_hash",
    )
    .withColumn("ind_en_mora", F.col("dias_mora_act") > 0)
    .withColumn(
        "rango_mora",
        F.when(F.col("dias_mora_act") <= 0, "AL_DIA")
        .when(F.col("dias_mora_act") <= 30, "MORA_1_30")
        .when(F.col("dias_mora_act") <= 60, "MORA_31_60")
        .when(F.col("dias_mora_act") <= 90, "MORA_61_90")
        .otherwise("MORA_MAYOR_90"),
    )
)

fact_comisiones = comisiones.select(
    "id_comision",
    F.col("id_cli").alias("cliente_key"),
    F.col("cod_prod").alias("producto_key"),
    F.date_format("fec_cobro", "yyyyMMdd").cast("int").alias("fecha_key"),
    "vr_comision",
    "tip_comision",
    "estado_cobro",
    "_record_hash",
)

fact_movimientos_rows = publish_gold(
    fact_movimientos, "fact_movimientos", ["id_mov"], "FACT"
)
fact_obligaciones_rows = publish_gold(
    fact_obligaciones, "fact_obligaciones", ["id_oblig"], "FACT"
)
fact_comisiones_rows = publish_gold(
    fact_comisiones, "fact_comisiones", ["id_comision"], "FACT"
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Marts analiticos

# COMMAND ----------

movimientos_cliente = fact_movimientos.groupBy("cliente_key").agg(
    F.count("id_mov").alias("cantidad_movimientos"),
    F.round(F.sum("vr_mov"), 2).alias("valor_total_movimientos"),
    F.round(F.avg("vr_mov"), 2).alias("valor_promedio_movimiento"),
    F.sum(F.col("ind_sospechoso").cast("int")).alias("movimientos_sospechosos"),
    F.countDistinct("producto_key").alias("productos_con_movimiento"),
    F.max("fecha_key").alias("ultima_fecha_movimiento_key"),
)

obligaciones_cliente = fact_obligaciones.groupBy("cliente_key").agg(
    F.count("id_oblig").alias("cantidad_obligaciones"),
    F.round(F.sum("vr_aprobado"), 2).alias("valor_total_aprobado"),
    F.round(F.sum("sdo_capital"), 2).alias("saldo_total_capital"),
    F.sum(F.col("ind_en_mora").cast("int")).alias("obligaciones_en_mora"),
    F.max("dias_mora_act").alias("max_dias_mora"),
)

comisiones_cliente = fact_comisiones.groupBy("cliente_key").agg(
    F.count("id_comision").alias("cantidad_comisiones"),
    F.round(F.sum("vr_comision"), 2).alias("valor_total_comisiones"),
)

mart_cliente_360 = (
    dim_cliente.join(movimientos_cliente, "cliente_key", "left")
    .join(obligaciones_cliente, "cliente_key", "left")
    .join(comisiones_cliente, "cliente_key", "left")
    .fillna(
        0,
        subset=[
            "cantidad_movimientos",
            "valor_total_movimientos",
            "valor_promedio_movimiento",
            "movimientos_sospechosos",
            "productos_con_movimiento",
            "cantidad_obligaciones",
            "valor_total_aprobado",
            "saldo_total_capital",
            "obligaciones_en_mora",
            "max_dias_mora",
            "cantidad_comisiones",
            "valor_total_comisiones",
        ],
    )
    .withColumn(
        "porcentaje_movimientos_sospechosos",
        F.when(
            F.col("cantidad_movimientos") > 0,
            F.round(
                100
                * F.col("movimientos_sospechosos")
                / F.col("cantidad_movimientos"),
                2,
            ),
        ).otherwise(F.lit(0.0)),
    )
    .withColumn(
        "nivel_alerta_cliente",
        F.when(
            (F.col("max_dias_mora") > 90)
            | (F.col("movimientos_sospechosos") >= 10),
            "ALTO",
        )
        .when(
            (F.col("max_dias_mora") > 30)
            | (F.col("movimientos_sospechosos") > 0),
            "MEDIO",
        )
        .otherwise("BAJO"),
    )
)

movimientos_producto = fact_movimientos.groupBy("producto_key").agg(
    F.count("id_mov").alias("cantidad_movimientos"),
    F.round(F.sum("vr_mov"), 2).alias("valor_total_movimientos"),
    F.sum(F.col("ind_sospechoso").cast("int")).alias("movimientos_sospechosos"),
    F.countDistinct("cliente_key").alias("clientes_con_movimientos"),
)

obligaciones_producto = fact_obligaciones.groupBy("producto_key").agg(
    F.count("id_oblig").alias("cantidad_obligaciones"),
    F.round(F.sum("vr_desembolsado"), 2).alias("valor_total_desembolsado"),
    F.round(F.sum("sdo_capital"), 2).alias("saldo_total_capital"),
    F.sum(F.col("ind_en_mora").cast("int")).alias("obligaciones_en_mora"),
)

comisiones_producto = fact_comisiones.groupBy("producto_key").agg(
    F.count("id_comision").alias("cantidad_comisiones"),
    F.round(F.sum("vr_comision"), 2).alias("valor_total_comisiones"),
)

mart_producto_rendimiento = (
    dim_producto.join(movimientos_producto, "producto_key", "left")
    .join(obligaciones_producto, "producto_key", "left")
    .join(comisiones_producto, "producto_key", "left")
    .fillna(
        0,
        subset=[
            "cantidad_movimientos",
            "valor_total_movimientos",
            "movimientos_sospechosos",
            "clientes_con_movimientos",
            "cantidad_obligaciones",
            "valor_total_desembolsado",
            "saldo_total_capital",
            "obligaciones_en_mora",
            "cantidad_comisiones",
            "valor_total_comisiones",
        ],
    )
)

clientes_kpi = dim_cliente.agg(
    F.count("cliente_key").alias("total_clientes"),
    F.sum((F.col("estado_cli") == "ACTIVO").cast("int")).alias("clientes_activos"),
)

movimientos_kpi = fact_movimientos.agg(
    F.count("id_mov").alias("total_movimientos"),
    F.round(F.sum("vr_mov"), 2).alias("valor_total_movimientos"),
    F.sum(F.col("ind_sospechoso").cast("int")).alias("movimientos_sospechosos"),
)

obligaciones_kpi = fact_obligaciones.agg(
    F.count("id_oblig").alias("total_obligaciones"),
    F.round(F.sum("sdo_capital"), 2).alias("saldo_total_cartera"),
    F.sum(F.col("ind_en_mora").cast("int")).alias("obligaciones_en_mora"),
)

comisiones_kpi = fact_comisiones.agg(
    F.count("id_comision").alias("total_comisiones"),
    F.round(F.sum("vr_comision"), 2).alias("ingreso_total_comisiones"),
)

kpi_resumen_bancario = (
    clientes_kpi.crossJoin(movimientos_kpi)
    .crossJoin(obligaciones_kpi)
    .crossJoin(comisiones_kpi)
    .withColumn(
        "porcentaje_movimientos_sospechosos",
        F.round(
            100 * F.col("movimientos_sospechosos") / F.col("total_movimientos"),
            2,
        ),
    )
    .withColumn(
        "porcentaje_obligaciones_en_mora",
        F.round(
            100 * F.col("obligaciones_en_mora") / F.col("total_obligaciones"),
            2,
        ),
    )
    .withColumn("fecha_corte", F.to_date(F.lit(ANALYSIS_END_DATE)))
    .withColumn("run_id", F.lit(RUN_ID))
)

mart_cliente_rows = publish_gold(
    mart_cliente_360, "mart_cliente_360", ["cliente_key"], "MART"
)
mart_producto_rows = publish_gold(
    mart_producto_rendimiento,
    "mart_producto_rendimiento",
    ["producto_key"],
    "MART",
)
kpi_rows = publish_gold(
    kpi_resumen_bancario, "kpi_resumen_bancario", ["run_id"], "MART"
)


# COMMAND ----------
# MAGIC %md
# MAGIC ## Conciliaciones y metricas de ejecucion

# COMMAND ----------

expected_fact_movimientos = movimientos.filter(F.col("ind_fecha_rango_valido")).count()

if fact_movimientos_rows != expected_fact_movimientos:
    raise RuntimeError("El conteo de movimientos Gold no coincide con Silver valido.")
if fact_obligaciones_rows != obligaciones.count():
    raise RuntimeError("El conteo de obligaciones Gold no coincide con Silver.")
if fact_comisiones_rows != comisiones.count():
    raise RuntimeError("El conteo de comisiones Gold no coincide con Silver.")
if dim_cliente_rows != clientes.count():
    raise RuntimeError("El conteo de clientes Gold no coincide con Silver.")
if dim_producto_rows != productos.count():
    raise RuntimeError("El conteo de productos Gold no coincide con Silver.")
if dim_sucursal_rows != sucursales.count():
    raise RuntimeError("El conteo de sucursales Gold no coincide con Silver.")

assert_no_orphans(
    fact_movimientos, dim_cliente, "cliente_key", "cliente_key", "movimiento-cliente"
)
assert_no_orphans(
    fact_movimientos,
    dim_producto,
    "producto_key",
    "producto_key",
    "movimiento-producto",
)
assert_no_orphans(
    fact_obligaciones,
    dim_cliente,
    "cliente_key",
    "cliente_key",
    "obligacion-cliente",
)
assert_no_orphans(
    fact_obligaciones,
    dim_producto,
    "producto_key",
    "producto_key",
    "obligacion-producto",
)
assert_no_orphans(
    fact_comisiones, dim_cliente, "cliente_key", "cliente_key", "comision-cliente"
)
assert_no_orphans(
    fact_comisiones,
    dim_producto,
    "producto_key",
    "producto_key",
    "comision-producto",
)
assert_no_orphans(
    fact_movimientos, dim_fecha, "fecha_key", "fecha_key", "movimiento-fecha"
)
assert_no_orphans(
    fact_obligaciones,
    dim_fecha,
    "fecha_desembolso_key",
    "fecha_key",
    "obligacion-fecha-desembolso",
)
assert_no_orphans(
    fact_obligaciones,
    dim_fecha,
    "fecha_venc_key",
    "fecha_key",
    "obligacion-fecha-vencimiento",
)
assert_no_orphans(
    fact_comisiones, dim_fecha, "fecha_key", "fecha_key", "comision-fecha"
)

silver_movement_total = movimientos.filter(F.col("ind_fecha_rango_valido")).agg(
    F.sum("vr_mov").alias("total")
).first()["total"]
gold_movement_total = fact_movimientos.agg(F.sum("vr_mov").alias("total")).first()[
    "total"
]
assert_decimal_equal(
    silver_movement_total, gold_movement_total, "valor_total_movimientos"
)

silver_balance_total = obligaciones.agg(F.sum("sdo_capital").alias("total")).first()[
    "total"
]
gold_balance_total = fact_obligaciones.agg(F.sum("sdo_capital").alias("total")).first()[
    "total"
]
assert_decimal_equal(silver_balance_total, gold_balance_total, "saldo_total_cartera")

silver_commission_total = comisiones.agg(
    F.sum("vr_comision").alias("total")
).first()["total"]
gold_commission_total = fact_comisiones.agg(
    F.sum("vr_comision").alias("total")
).first()["total"]
assert_decimal_equal(
    silver_commission_total, gold_commission_total, "ingreso_total_comisiones"
)

metrics_df = spark.createDataFrame(gold_metrics).select(
    "run_id",
    "table_name",
    "table_type",
    "row_count",
    "processed_at_utc",
)

if metrics_df.count() != 10:
    raise RuntimeError("No se generaron metricas para los diez objetos Gold.")

(
    metrics_df.write.format("delta")
    .mode("append")
    .saveAsTable(f"{GOLD_SCHEMA}.gold_run_metrics")
)

reconciliation_df = spark.createDataFrame(
    [
        ("conteo_fact_movimientos", expected_fact_movimientos, fact_movimientos_rows),
        ("conteo_fact_obligaciones", obligaciones.count(), fact_obligaciones_rows),
        ("conteo_fact_comisiones", comisiones.count(), fact_comisiones_rows),
        ("conteo_dim_cliente", clientes.count(), dim_cliente_rows),
        ("conteo_dim_producto", productos.count(), dim_producto_rows),
        ("conteo_dim_sucursal", sucursales.count(), dim_sucursal_rows),
    ],
    ["control", "valor_silver", "valor_gold"],
).withColumn("resultado", F.col("valor_silver") == F.col("valor_gold"))

print(f"GOLD_RUN_ID: {RUN_ID}")
print("PROCESAMIENTO SILVER -> GOLD: SUCCESS")
display(metrics_df.orderBy("table_type", "table_name"))
display(reconciliation_df.orderBy("control"))
display(kpi_resumen_bancario)