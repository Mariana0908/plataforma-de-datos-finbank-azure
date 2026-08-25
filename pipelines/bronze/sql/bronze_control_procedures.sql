SET NOCOUNT ON;
GO

/* ============================================================
   Obtener las tablas activas
   ============================================================ */

CREATE OR ALTER PROCEDURE ctl.usp_get_ingestion_config
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        source_schema,
        source_table,
        load_strategy,
        primary_key_column,
        watermark_column,
        last_change_version,
        last_watermark_value,
        initial_load_completed
    FROM ctl.ingestion_config
    WHERE is_active = 1
    ORDER BY source_table;
END;
GO

/* ============================================================
   Construir consulta y límite de la extracción
   ============================================================ */

CREATE OR ALTER PROCEDURE ctl.usp_get_extract_command
    @source_schema SYSNAME,
    @source_table  SYSNAME
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @load_strategy          VARCHAR(30),
        @primary_key_column     SYSNAME,
        @watermark_column       SYSNAME,
        @last_change_version    BIGINT,
        @last_watermark_value   BIGINT,
        @initial_completed      BIT,
        @new_watermark          BIGINT,
        @minimum_valid_version  BIGINT,
        @object_id              INT,
        @qualified_table        NVARCHAR(600),
        @source_query           NVARCHAR(MAX);

    SELECT
        @load_strategy = load_strategy,
        @primary_key_column = primary_key_column,
        @watermark_column = watermark_column,
        @last_change_version = last_change_version,
        @last_watermark_value = last_watermark_value,
        @initial_completed = initial_load_completed
    FROM ctl.ingestion_config
    WHERE source_schema = @source_schema
      AND source_table = @source_table
      AND is_active = 1;

    IF @load_strategy IS NULL
    BEGIN
        THROW 50001, 'La tabla no tiene una configuración de ingesta activa.', 1;
    END;

    SET @qualified_table =
        QUOTENAME(@source_schema) + N'.' + QUOTENAME(@source_table);

    SET @object_id = OBJECT_ID(@qualified_table);

    IF @object_id IS NULL
    BEGIN
        THROW 50002, 'La tabla fuente configurada no existe.', 1;
    END;

    IF @load_strategy = 'CHANGE_TRACKING'
    BEGIN
        SET @new_watermark =
            ISNULL(CHANGE_TRACKING_CURRENT_VERSION(), 0);

        IF @initial_completed = 0
        BEGIN
            SET @source_query =
                N'SELECT * FROM ' + @qualified_table + N';';
        END;
        ELSE
        BEGIN
            SET @minimum_valid_version =
                CHANGE_TRACKING_MIN_VALID_VERSION(@object_id);

            IF @last_change_version IS NULL
               OR @last_change_version < @minimum_valid_version
            BEGIN
                THROW 50003,
                    'La versión de Change Tracking dejó de ser válida. Se requiere una recarga completa.',
                    1;
            END;

            SET @source_query =
                N'SELECT source.* ' +
                N'FROM CHANGETABLE(CHANGES ' +
                @qualified_table + N', ' +
                CONVERT(NVARCHAR(30), @last_change_version) +
                N') AS changes ' +
                N'INNER JOIN ' + @qualified_table + N' AS source ' +
                N'ON source.' + QUOTENAME(@primary_key_column) +
                N' = changes.' + QUOTENAME(@primary_key_column) + N' ' +
                N'WHERE changes.SYS_CHANGE_OPERATION IN (''I'', ''U'') ' +
                N'AND changes.SYS_CHANGE_VERSION <= ' +
                CONVERT(NVARCHAR(30), @new_watermark) + N';';
        END;
    END;
    ELSE IF @load_strategy = 'APPEND_WATERMARK'
    BEGIN
        IF @source_table <> 'TB_MOV_FINANCIEROS'
        BEGIN
            THROW 50004,
                'La estrategia append-only no está implementada para esta tabla.',
                1;
        END;

        SELECT
            @new_watermark = ISNULL(MAX(id_mov), 0)
        FROM dbo.TB_MOV_FINANCIEROS;

        IF @initial_completed = 0
        BEGIN
            SET @source_query =
                N'SELECT * FROM ' + @qualified_table +
                N' WHERE ' + QUOTENAME(@watermark_column) +
                N' <= ' + CONVERT(NVARCHAR(30), @new_watermark) + N';';
        END;
        ELSE
        BEGIN
            SET @source_query =
                N'SELECT * FROM ' + @qualified_table +
                N' WHERE ' + QUOTENAME(@watermark_column) +
                N' > ' +
                CONVERT(
                    NVARCHAR(30),
                    ISNULL(@last_watermark_value, 0)
                ) +
                N' AND ' + QUOTENAME(@watermark_column) +
                N' <= ' +
                CONVERT(NVARCHAR(30), @new_watermark) + N';';
        END;
    END;
    ELSE
    BEGIN
        THROW 50005, 'Estrategia de ingesta no soportada.', 1;
    END;

    SELECT
        @source_schema AS source_schema,
        @source_table AS source_table,
        @load_strategy AS load_strategy,
        @initial_completed AS initial_load_completed,
        @new_watermark AS new_watermark,
        @source_query AS source_query;
END;
GO

/* ============================================================
   Registrar inicio
   ============================================================ */

CREATE OR ALTER PROCEDURE ctl.usp_start_ingestion_run
    @pipeline_run_id VARCHAR(100),
    @batch_id        VARCHAR(100),
    @source_table    SYSNAME,
    @started_at_utc  DATETIME2(3) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (
        SELECT 1
        FROM ctl.pipeline_run_log
        WHERE pipeline_run_id = @pipeline_run_id
          AND source_table = @source_table
    )
    BEGIN
        INSERT INTO ctl.pipeline_run_log
        (
            pipeline_run_id,
            batch_id,
            source_table,
            started_at_utc,
            status
        )
        VALUES
        (
            @pipeline_run_id,
            @batch_id,
            @source_table,
            ISNULL(@started_at_utc, SYSUTCDATETIME()),
            'STARTED'
        );
    END;
END;
GO

/* ============================================================
   Registrar finalización y actualizar watermark
   ============================================================ */

CREATE OR ALTER PROCEDURE ctl.usp_complete_ingestion_run
    @pipeline_run_id   VARCHAR(100),
    @source_table      SYSNAME,
    @new_watermark     BIGINT,
    @rows_read         BIGINT,
    @rows_copied       BIGINT,
    @bytes_written     BIGINT,
    @duration_seconds  INT,
    @output_path       NVARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    UPDATE ctl.pipeline_run_log
    SET
        finished_at_utc = SYSUTCDATETIME(),
        status = 'SUCCEEDED',
        rows_read = @rows_read,
        rows_copied = @rows_copied,
        bytes_written = @bytes_written,
        duration_seconds = @duration_seconds,
        output_path = @output_path,
        error_message = NULL
    WHERE pipeline_run_id = @pipeline_run_id
      AND source_table = @source_table;

    IF @@ROWCOUNT = 0
    BEGIN
        THROW 50006,
            'No existe un log STARTED para la tabla y ejecución indicadas.',
            1;
    END;

    UPDATE ctl.ingestion_config
    SET
        last_change_version =
            CASE
                WHEN load_strategy = 'CHANGE_TRACKING'
                    THEN @new_watermark
                ELSE last_change_version
            END,
        last_watermark_value =
            CASE
                WHEN load_strategy = 'APPEND_WATERMARK'
                    THEN @new_watermark
                ELSE last_watermark_value
            END,
        initial_load_completed = 1,
        updated_at_utc = SYSUTCDATETIME()
    WHERE source_table = @source_table
      AND is_active = 1;

    COMMIT TRANSACTION;
END;
GO

/* ============================================================
   Registrar fallo y tabla de errores
   ============================================================ */

CREATE OR ALTER PROCEDURE ctl.usp_fail_ingestion_run
    @pipeline_run_id  VARCHAR(100),
    @batch_id         VARCHAR(100),
    @source_table     SYSNAME,
    @activity_name    NVARCHAR(200),
    @error_code       NVARCHAR(100),
    @error_message    NVARCHAR(2000),
    @error_details    NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    UPDATE ctl.pipeline_run_log
    SET
        finished_at_utc = SYSUTCDATETIME(),
        status = 'FAILED',
        error_message = @error_message
    WHERE pipeline_run_id = @pipeline_run_id
      AND source_table = @source_table;

    IF @@ROWCOUNT = 0
    BEGIN
        INSERT INTO ctl.pipeline_run_log
        (
            pipeline_run_id,
            batch_id,
            source_table,
            started_at_utc,
            finished_at_utc,
            status,
            error_message
        )
        VALUES
        (
            @pipeline_run_id,
            @batch_id,
            @source_table,
            SYSUTCDATETIME(),
            SYSUTCDATETIME(),
            'FAILED',
            @error_message
        );
    END;

    INSERT INTO ctl.pipeline_error
    (
        pipeline_run_id,
        batch_id,
        source_table,
        activity_name,
        error_code,
        error_message,
        error_details
    )
    VALUES
    (
        @pipeline_run_id,
        @batch_id,
        @source_table,
        @activity_name,
        @error_code,
        @error_message,
        @error_details
    );

    COMMIT TRANSACTION;
END;
GO