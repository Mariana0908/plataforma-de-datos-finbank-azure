-- Validaciones reproducibles de la capa Silver de FinBank.
-- Ejecutar cada bloque por separado en Databricks SQL.

USE CATALOG dbw_finbank_dev_eus;

-- 1. Conteos de las seis tablas Delta Silver.
SELECT 'tb_clientes_core' AS tabla, COUNT(*) AS cantidad
FROM silver.tb_clientes_core
UNION ALL
SELECT 'tb_productos_cat', COUNT(*)
FROM silver.tb_productos_cat
UNION ALL
SELECT 'tb_sucursales_red', COUNT(*)
FROM silver.tb_sucursales_red
UNION ALL
SELECT 'tb_obligaciones', COUNT(*)
FROM silver.tb_obligaciones
UNION ALL
SELECT 'tb_comisiones_log', COUNT(*)
FROM silver.tb_comisiones_log
UNION ALL
SELECT 'tb_mov_financieros', COUNT(*)
FROM silver.tb_mov_financieros;

-- 2. Calidad y estandarizacion de movimientos.
SELECT
    COUNT(*) AS total_movimientos_silver,
    COUNT(DISTINCT id_mov) AS ids_movimiento_unicos,
    COUNT_IF(NOT ind_fecha_rango_valido) AS fechas_fuera_rango,
    COUNT_IF(NOT ind_canal_valido) AS canales_invalidos_detectados,
    COUNT_IF(cod_canal = 'DESCONOCIDO') AS canales_mapeados_desconocido,
    COUNT_IF(ind_sospechoso) AS movimientos_sospechosos
FROM silver.tb_mov_financieros;

-- 3. Integridad referencial de las tablas transaccionales.
SELECT
    (
        SELECT COUNT(*)
        FROM silver.tb_mov_financieros mov
        LEFT JOIN silver.tb_clientes_core cli ON mov.id_cli = cli.id_cli
        WHERE cli.id_cli IS NULL
    ) AS movimientos_sin_cliente,
    (
        SELECT COUNT(*)
        FROM silver.tb_mov_financieros mov
        LEFT JOIN silver.tb_productos_cat prod ON mov.cod_prod = prod.cod_prod
        WHERE prod.cod_prod IS NULL
    ) AS movimientos_sin_producto,
    (
        SELECT COUNT(*)
        FROM silver.tb_obligaciones obl
        LEFT JOIN silver.tb_clientes_core cli ON obl.id_cli = cli.id_cli
        WHERE cli.id_cli IS NULL
    ) AS obligaciones_sin_cliente,
    (
        SELECT COUNT(*)
        FROM silver.tb_obligaciones obl
        LEFT JOIN silver.tb_productos_cat prod ON obl.cod_prod = prod.cod_prod
        WHERE prod.cod_prod IS NULL
    ) AS obligaciones_sin_producto,
    (
        SELECT COUNT(*)
        FROM silver.tb_comisiones_log com
        LEFT JOIN silver.tb_clientes_core cli ON com.id_cli = cli.id_cli
        WHERE cli.id_cli IS NULL
    ) AS comisiones_sin_cliente,
    (
        SELECT COUNT(*)
        FROM silver.tb_comisiones_log com
        LEFT JOIN silver.tb_productos_cat prod ON com.cod_prod = prod.cod_prod
        WHERE prod.cod_prod IS NULL
    ) AS comisiones_sin_producto;

-- 4. Resumen auditable de reglas de calidad.
SELECT
    table_name,
    quality_rule,
    rejected_rows,
    run_id,
    processed_at_utc
FROM quality.rule_summary
ORDER BY table_name, quality_rule;

-- 5. Ultimas dos ejecuciones para comprobar idempotencia.
WITH ejecuciones AS
(
    SELECT
        run_id,
        MAX(processed_at_utc) AS processed_at_utc,
        COUNT(DISTINCT table_name) AS tablas_procesadas,
        SUM(bronze_rows) AS total_bronze,
        SUM(silver_rows) AS total_silver,
        SUM(quarantined_rows) AS total_cuarentena
    FROM quality.silver_run_metrics
    GROUP BY run_id
),
ultimas_ejecuciones AS
(
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY processed_at_utc DESC) AS orden
    FROM ejecuciones
)
SELECT
    run_id,
    processed_at_utc,
    tablas_procesadas,
    total_bronze,
    total_silver,
    total_cuarentena
FROM ultimas_ejecuciones
WHERE orden <= 2
ORDER BY processed_at_utc DESC;

-- 6. Muestra analitica de movimientos sospechosos.
SELECT
    id_mov,
    id_cli,
    fec_mov,
    vr_mov,
    promedio_vr_mov_30d,
    desv_vr_mov_30d,
    cantidad_mov_30d,
    ind_sospechoso
FROM silver.tb_mov_financieros
WHERE ind_sospechoso
ORDER BY fec_mov DESC, vr_mov DESC
LIMIT 20;