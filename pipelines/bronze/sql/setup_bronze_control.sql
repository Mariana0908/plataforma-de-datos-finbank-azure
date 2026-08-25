SET NOCOUNT ON;
GO

/* ============================================================
   Habilitación de Change Tracking en la base actual
   ============================================================ */

DECLARE @database_sql NVARCHAR(MAX);

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_databases
    WHERE database_id = DB_ID()
)
BEGIN
    SET @database_sql =
        N'ALTER DATABASE ' + QUOTENAME(DB_NAME()) +
        N' SET CHANGE_TRACKING = ON
        (
            CHANGE_RETENTION = 7 DAYS,
            AUTO_CLEANUP = ON
        );';

    EXEC sys.sp_executesql @database_sql;
END;
GO

/* ============================================================
   Change Tracking para tablas con llave primaria
   ============================================================ */

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_tables
    WHERE object_id = OBJECT_ID(N'dbo.TB_CLIENTES_CORE')
)
BEGIN
    ALTER TABLE dbo.TB_CLIENTES_CORE
        ENABLE CHANGE_TRACKING
        WITH (TRACK_COLUMNS_UPDATED = ON);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_tables
    WHERE object_id = OBJECT_ID(N'dbo.TB_PRODUCTOS_CAT')
)
BEGIN
    ALTER TABLE dbo.TB_PRODUCTOS_CAT
        ENABLE CHANGE_TRACKING
        WITH (TRACK_COLUMNS_UPDATED = ON);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_tables
    WHERE object_id = OBJECT_ID(N'dbo.TB_SUCURSALES_RED')
)
BEGIN
    ALTER TABLE dbo.TB_SUCURSALES_RED
        ENABLE CHANGE_TRACKING
        WITH (TRACK_COLUMNS_UPDATED = ON);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_tables
    WHERE object_id = OBJECT_ID(N'dbo.TB_OBLIGACIONES')
)
BEGIN
    ALTER TABLE dbo.TB_OBLIGACIONES
        ENABLE CHANGE_TRACKING
        WITH (TRACK_COLUMNS_UPDATED = ON);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.change_tracking_tables
    WHERE object_id = OBJECT_ID(N'dbo.TB_COMISIONES_LOG')
)
BEGIN
    ALTER TABLE dbo.TB_COMISIONES_LOG
        ENABLE CHANGE_TRACKING
        WITH (TRACK_COLUMNS_UPDATED = ON);
END;
GO

/* ============================================================
   Esquema y configuración operacional
   ============================================================ */

IF SCHEMA_ID(N'ctl') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA ctl AUTHORIZATION dbo;');
END;
GO

IF OBJECT_ID(N'ctl.ingestion_config', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.ingestion_config
    (
        source_schema           SYSNAME       NOT NULL,
        source_table            SYSNAME       NOT NULL,
        load_strategy           VARCHAR(30)   NOT NULL,
        primary_key_column      SYSNAME       NULL,
        watermark_column        SYSNAME       NULL,
        last_change_version     BIGINT        NULL,
        last_watermark_value    BIGINT        NULL,
        initial_load_completed  BIT           NOT NULL
            CONSTRAINT DF_ingestion_initial DEFAULT (0),
        is_active               BIT           NOT NULL
            CONSTRAINT DF_ingestion_active DEFAULT (1),
        updated_at_utc          DATETIME2(0)  NOT NULL
            CONSTRAINT DF_ingestion_updated DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ingestion_config
            PRIMARY KEY (source_schema, source_table),

        CONSTRAINT CK_ingestion_strategy
            CHECK (load_strategy IN (
                'CHANGE_TRACKING',
                'APPEND_WATERMARK'
            ))
    );
END;
GO

MERGE ctl.ingestion_config AS target
USING (
    VALUES
        ('dbo', 'TB_CLIENTES_CORE',   'CHANGE_TRACKING',  'id_cli',      NULL),
        ('dbo', 'TB_PRODUCTOS_CAT',   'CHANGE_TRACKING',  'cod_prod',    NULL),
        ('dbo', 'TB_SUCURSALES_RED',  'CHANGE_TRACKING',  'cod_suc',     NULL),
        ('dbo', 'TB_MOV_FINANCIEROS', 'APPEND_WATERMARK', NULL,          'id_mov'),
        ('dbo', 'TB_OBLIGACIONES',    'CHANGE_TRACKING',  'id_oblig',    NULL),
        ('dbo', 'TB_COMISIONES_LOG',  'CHANGE_TRACKING',  'id_comision', NULL)
) AS source (
    source_schema,
    source_table,
    load_strategy,
    primary_key_column,
    watermark_column
)
ON target.source_schema = source.source_schema
AND target.source_table = source.source_table

WHEN MATCHED THEN
    UPDATE SET
        target.load_strategy = source.load_strategy,
        target.primary_key_column = source.primary_key_column,
        target.watermark_column = source.watermark_column,
        target.is_active = 1,
        target.updated_at_utc = SYSUTCDATETIME()

WHEN NOT MATCHED THEN
    INSERT (
        source_schema,
        source_table,
        load_strategy,
        primary_key_column,
        watermark_column
    )
    VALUES (
        source.source_schema,
        source.source_table,
        source.load_strategy,
        source.primary_key_column,
        source.watermark_column
    );
GO

/* ============================================================
   Log de ejecuciones
   ============================================================ */

IF OBJECT_ID(N'ctl.pipeline_run_log', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.pipeline_run_log
    (
        log_id              BIGINT IDENTITY(1, 1) NOT NULL,
        pipeline_run_id     VARCHAR(100)           NOT NULL,
        batch_id            VARCHAR(100)           NOT NULL,
        source_table        SYSNAME                NOT NULL,
        started_at_utc      DATETIME2(3)           NOT NULL,
        finished_at_utc     DATETIME2(3)           NULL,
        status              VARCHAR(20)            NOT NULL,
        rows_read           BIGINT                 NULL,
        rows_copied         BIGINT                 NULL,
        bytes_written       BIGINT                 NULL,
        duration_seconds    INT                    NULL,
        output_path         NVARCHAR(500)          NULL,
        error_message       NVARCHAR(2000)         NULL,
        created_at_utc      DATETIME2(0)           NOT NULL
            CONSTRAINT DF_pipeline_log_created
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_pipeline_run_log PRIMARY KEY (log_id),

        CONSTRAINT CK_pipeline_log_status CHECK (
            status IN ('STARTED', 'SUCCEEDED', 'FAILED', 'SKIPPED')
        )
    );
END;
GO

/* ============================================================
   Tabla de errores
   ============================================================ */

IF OBJECT_ID(N'ctl.pipeline_error', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.pipeline_error
    (
        error_id          BIGINT IDENTITY(1, 1) NOT NULL,
        pipeline_run_id   VARCHAR(100)           NOT NULL,
        batch_id          VARCHAR(100)           NOT NULL,
        source_table      SYSNAME                NULL,
        activity_name     NVARCHAR(200)          NULL,
        error_code        NVARCHAR(100)          NULL,
        error_message     NVARCHAR(2000)         NOT NULL,
        error_details     NVARCHAR(MAX)          NULL,
        occurred_at_utc   DATETIME2(3)           NOT NULL
            CONSTRAINT DF_pipeline_error_date
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_pipeline_error PRIMARY KEY (error_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_pipeline_run_log_run_table'
      AND object_id = OBJECT_ID(N'ctl.pipeline_run_log')
)
BEGIN
    CREATE INDEX IX_pipeline_run_log_run_table
        ON ctl.pipeline_run_log (
            pipeline_run_id,
            source_table
        );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_pipeline_error_run'
      AND object_id = OBJECT_ID(N'ctl.pipeline_error')
)
BEGIN
    CREATE INDEX IX_pipeline_error_run
        ON ctl.pipeline_error (
            pipeline_run_id,
            occurred_at_utc
        );
END;
GO

SELECT
    source_schema,
    source_table,
    load_strategy,
    primary_key_column,
    watermark_column,
    initial_load_completed,
    is_active
FROM ctl.ingestion_config
ORDER BY source_table;
GO