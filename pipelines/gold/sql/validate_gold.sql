-- Validaciones reproducibles del modelo analitico Gold de FinBank.
-- Ejecutar cada bloque por separado en Databricks SQL.

USE CATALOG dbw_finbank_dev_eus;

-- 1. Objetos persistentes del esquema Gold.
SHOW TABLES IN gold;

-- 2. Conteos de dimensiones, hechos y marts.
SELECT 'dim_cliente' AS tabla, COUNT(*) AS cantidad FROM gold.dim_cliente
UNION ALL
SELECT 'dim_fecha', COUNT(*) FROM gold.dim_fecha
UNION ALL
SELECT 'dim_producto', COUNT(*) FROM gold.dim_producto
UNION ALL
SELECT 'dim_sucursal', COUNT(*) FROM gold.dim_sucursal
UNION ALL
SELECT 'fact_comisiones', COUNT(*) FROM gold.fact_comisiones
UNION ALL
SELECT 'fact_movimientos', COUNT(*) FROM gold.fact_movimientos
UNION ALL
SELECT 'fact_obligaciones', COUNT(*) FROM gold.fact_obligaciones
UNION ALL
SELECT 'kpi_resumen_bancario', COUNT(*) FROM gold.kpi_resumen_bancario
UNION ALL
SELECT 'mart_cliente_360', COUNT(*) FROM gold.mart_cliente_360
UNION ALL
SELECT 'mart_producto_rendimiento', COUNT(*)
FROM gold.mart_producto_rendimiento
ORDER BY tabla;

-- 3. KPI ejecutivos.
SELECT
    total_clientes,
    clientes_activos,
    total_movimientos,
    movimientos_sospechosos,
    porcentaje_movimientos_sospechosos,
    total_obligaciones,
    obligaciones_en_mora,
    porcentaje_obligaciones_en_mora,
    saldo_total_cartera,
    ingreso_total_comisiones,
    fecha_corte
FROM gold.kpi_resumen_bancario;

-- 4. Integridad del modelo dimensional.
SELECT 'movimientos_sin_cliente' AS control, COUNT(*) AS inconsistencias
FROM gold.fact_movimientos fact
LEFT JOIN gold.dim_cliente dim ON fact.cliente_key = dim.cliente_key
WHERE dim.cliente_key IS NULL
UNION ALL
SELECT 'movimientos_sin_producto', COUNT(*)
FROM gold.fact_movimientos fact
LEFT JOIN gold.dim_producto dim ON fact.producto_key = dim.producto_key
WHERE dim.producto_key IS NULL
UNION ALL
SELECT 'movimientos_sin_fecha', COUNT(*)
FROM gold.fact_movimientos fact
LEFT JOIN gold.dim_fecha dim ON fact.fecha_key = dim.fecha_key
WHERE dim.fecha_key IS NULL
UNION ALL
SELECT 'obligaciones_sin_cliente', COUNT(*)
FROM gold.fact_obligaciones fact
LEFT JOIN gold.dim_cliente dim ON fact.cliente_key = dim.cliente_key
WHERE dim.cliente_key IS NULL
UNION ALL
SELECT 'obligaciones_sin_producto', COUNT(*)
FROM gold.fact_obligaciones fact
LEFT JOIN gold.dim_producto dim ON fact.producto_key = dim.producto_key
WHERE dim.producto_key IS NULL
UNION ALL
SELECT 'obligaciones_sin_fecha_desembolso', COUNT(*)
FROM gold.fact_obligaciones fact
LEFT JOIN gold.dim_fecha dim ON fact.fecha_desembolso_key = dim.fecha_key
WHERE dim.fecha_key IS NULL
UNION ALL
SELECT 'obligaciones_sin_fecha_vencimiento', COUNT(*)
FROM gold.fact_obligaciones fact
LEFT JOIN gold.dim_fecha dim ON fact.fecha_venc_key = dim.fecha_key
WHERE dim.fecha_key IS NULL
UNION ALL
SELECT 'comisiones_sin_cliente', COUNT(*)
FROM gold.fact_comisiones fact
LEFT JOIN gold.dim_cliente dim ON fact.cliente_key = dim.cliente_key
WHERE dim.cliente_key IS NULL
UNION ALL
SELECT 'comisiones_sin_producto', COUNT(*)
FROM gold.fact_comisiones fact
LEFT JOIN gold.dim_producto dim ON fact.producto_key = dim.producto_key
WHERE dim.producto_key IS NULL
UNION ALL
SELECT 'comisiones_sin_fecha', COUNT(*)
FROM gold.fact_comisiones fact
LEFT JOIN gold.dim_fecha dim ON fact.fecha_key = dim.fecha_key
WHERE dim.fecha_key IS NULL
ORDER BY control;

-- 5. Minimizacion de datos personales.
SELECT
    SUM(
        CASE
            WHEN LOWER(column_name) IN (
                'nomb_cli',
                'apell_cli',
                'tip_doc',
                'num_doc',
                'fec_nac',
                'num_cuenta'
            ) THEN 1
            ELSE 0
        END
    ) AS columnas_personales_expuestas,
    COUNT_IF(LOWER(column_name) = 'num_cuenta_hash')
        AS columnas_cuenta_protegidas,
    COUNT(DISTINCT table_name) AS tablas_gold_inspeccionadas
FROM dbw_finbank_dev_eus.information_schema.columns
WHERE table_schema = 'gold';

-- 6. Segmentacion de alerta de clientes.
SELECT
    nivel_alerta_cliente,
    COUNT(*) AS cantidad_clientes,
    SUM(cantidad_movimientos) AS total_movimientos,
    SUM(movimientos_sospechosos) AS movimientos_sospechosos,
    SUM(obligaciones_en_mora) AS obligaciones_en_mora,
    ROUND(SUM(saldo_total_capital), 2) AS saldo_total_cartera,
    ROUND(SUM(valor_total_comisiones), 2) AS ingreso_total_comisiones
FROM gold.mart_cliente_360
GROUP BY nivel_alerta_cliente
ORDER BY
    CASE nivel_alerta_cliente
        WHEN 'ALTO' THEN 1
        WHEN 'MEDIO' THEN 2
        WHEN 'BAJO' THEN 3
        ELSE 4
    END;

-- 7. Productos con mayor saldo de cartera.
SELECT
    producto_key,
    desc_prod,
    tip_prod,
    clientes_con_movimientos,
    cantidad_movimientos,
    movimientos_sospechosos,
    cantidad_obligaciones,
    obligaciones_en_mora,
    ROUND(saldo_total_capital, 2) AS saldo_total_cartera,
    ROUND(valor_total_comisiones, 2) AS ingreso_total_comisiones
FROM gold.mart_producto_rendimiento
ORDER BY saldo_total_capital DESC
LIMIT 10;

-- 8. Idempotencia de las dos ejecuciones mas recientes.
WITH ejecuciones AS
(
    SELECT
        run_id,
        MAX(processed_at_utc) AS processed_at_utc
    FROM gold.gold_run_metrics
    GROUP BY run_id
),
ejecuciones_ordenadas AS
(
    SELECT
        run_id,
        processed_at_utc,
        ROW_NUMBER() OVER (ORDER BY processed_at_utc DESC) AS orden
    FROM ejecuciones
),
metricas_recientes AS
(
    SELECT
        met.table_name,
        met.row_count,
        eje.orden
    FROM gold.gold_run_metrics met
    INNER JOIN ejecuciones_ordenadas eje ON met.run_id = eje.run_id
    WHERE eje.orden <= 2
)
SELECT
    table_name,
    MAX(CASE WHEN orden = 1 THEN row_count END) AS ejecucion_reciente,
    MAX(CASE WHEN orden = 2 THEN row_count END) AS ejecucion_anterior,
    MAX(CASE WHEN orden = 1 THEN row_count END)
        = MAX(CASE WHEN orden = 2 THEN row_count END) AS resultado_idempotente
FROM metricas_recientes
GROUP BY table_name
ORDER BY table_name;
