-- ============================================================
-- Configuración de Unity Catalog para FinBank
-- ============================================================

USE CATALOG dbw_finbank_dev_eus;

-- Esquema para registrar el acceso gobernado a los archivos Bronze.
CREATE SCHEMA IF NOT EXISTS bronze
COMMENT 'Archivos fuente inmutables recibidos desde Azure SQL mediante Azure Data Factory';

-- Esquema de tablas Delta depuradas y estandarizadas.
CREATE SCHEMA IF NOT EXISTS silver
COMMENT 'Tablas Delta validadas y estandarizadas de FinBank'
MANAGED LOCATION 'abfss://silver@dlsfinbankdeveus2nctv.dfs.core.windows.net/tables';

-- Esquema para registros rechazados y resultados de calidad.
CREATE SCHEMA IF NOT EXISTS quality
COMMENT 'Registros en cuarentena y métricas de calidad de datos'
MANAGED LOCATION 'abfss://silver@dlsfinbankdeveus2nctv.dfs.core.windows.net/quality';

-- Esquema para modelos e indicadores analíticos.
CREATE SCHEMA IF NOT EXISTS gold
COMMENT 'Modelos analíticos e indicadores de negocio de FinBank'
MANAGED LOCATION 'abfss://gold@dlsfinbankdeveus2nctv.dfs.core.windows.net/tables';

-- Volumen de solo lectura sobre los archivos producidos por ADF.
CREATE EXTERNAL VOLUME IF NOT EXISTS bronze.raw_files
LOCATION 'abfss://bronze@dlsfinbankdeveus2nctv.dfs.core.windows.net/'
COMMENT 'Archivos Parquet de la capa Bronze producidos por Azure Data Factory';

-- Archivos operativos de Silver: reportes, checkpoints y manifiestos.
CREATE EXTERNAL VOLUME IF NOT EXISTS silver.operational_files
LOCATION 'abfss://silver@dlsfinbankdeveus2nctv.dfs.core.windows.net/operational'
COMMENT 'Archivos operativos y reportes del procesamiento Silver';

-- Exportaciones o archivos de consumo de la capa Gold.
CREATE EXTERNAL VOLUME IF NOT EXISTS gold.exports
LOCATION 'abfss://gold@dlsfinbankdeveus2nctv.dfs.core.windows.net/exports'
COMMENT 'Exportaciones de modelos e indicadores de la capa Gold';