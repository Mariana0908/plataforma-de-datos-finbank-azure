SET NOCOUNT ON;
GO

IF OBJECT_ID(N'dbo.TB_CLIENTES_CORE', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_CLIENTES_CORE
    (
        id_cli          INT            NOT NULL,
        nomb_cli        NVARCHAR(100)  NOT NULL,
        apell_cli       NVARCHAR(100)  NOT NULL,
        tip_doc         VARCHAR(10)    NOT NULL,
        num_doc         VARCHAR(30)    NOT NULL,
        fec_nac         DATE           NOT NULL,
        fec_alta        DATE           NOT NULL,
        cod_segmento    VARCHAR(20)    NOT NULL,
        score_buro      SMALLINT       NULL,
        ciudad_res      NVARCHAR(100)  NOT NULL,
        depto_res       NVARCHAR(100)  NOT NULL,
        estado_cli      VARCHAR(20)    NOT NULL,
        canal_adquis    VARCHAR(20)    NULL,
        CONSTRAINT PK_TB_CLIENTES_CORE PRIMARY KEY (id_cli)
    );
END;
GO

IF OBJECT_ID(N'dbo.TB_PRODUCTOS_CAT', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_PRODUCTOS_CAT
    (
        cod_prod          VARCHAR(10)    NOT NULL,
        desc_prod         NVARCHAR(150)  NOT NULL,
        tip_prod          VARCHAR(30)    NOT NULL,
        tasa_ea           DECIMAL(8, 2)  NOT NULL,
        plazo_max_meses   SMALLINT       NOT NULL,
        cuota_min         DECIMAL(18, 2) NOT NULL,
        comision_admin    DECIMAL(18, 2) NOT NULL,
        estado_prod       VARCHAR(20)    NOT NULL,
        CONSTRAINT PK_TB_PRODUCTOS_CAT PRIMARY KEY (cod_prod)
    );
END;
GO

IF OBJECT_ID(N'dbo.TB_SUCURSALES_RED', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_SUCURSALES_RED
    (
        cod_suc     VARCHAR(10)    NOT NULL,
        nom_suc     NVARCHAR(180)  NOT NULL,
        tip_punto   VARCHAR(30)    NOT NULL,
        ciudad      NVARCHAR(100)  NOT NULL,
        depto       NVARCHAR(100)  NOT NULL,
        latitud     DECIMAL(10, 6) NOT NULL,
        longitud    DECIMAL(10, 6) NOT NULL,
        activo      BIT            NOT NULL,
        CONSTRAINT PK_TB_SUCURSALES_RED PRIMARY KEY (cod_suc)
    );
END;
GO

IF OBJECT_ID(N'dbo.TB_MOV_FINANCIEROS', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_MOV_FINANCIEROS
    (
        id_mov           BIGINT         NOT NULL,
        id_cli           INT            NOT NULL,
        cod_prod         VARCHAR(10)    NOT NULL,
        num_cuenta       VARCHAR(30)    NOT NULL,
        fec_mov          DATE           NOT NULL,
        hra_mov          TIME(0)        NOT NULL,
        vr_mov           DECIMAL(18, 2) NOT NULL,
        tip_mov          VARCHAR(30)    NOT NULL,
        cod_canal        VARCHAR(30)    NOT NULL,
        cod_ciudad       VARCHAR(10)    NOT NULL,
        cod_estado_mov   VARCHAR(20)    NOT NULL,
        id_dispositivo   VARCHAR(30)    NULL,
        CONSTRAINT FK_MOV_CLIENTE FOREIGN KEY (id_cli)
            REFERENCES dbo.TB_CLIENTES_CORE (id_cli),
        CONSTRAINT FK_MOV_PRODUCTO FOREIGN KEY (cod_prod)
            REFERENCES dbo.TB_PRODUCTOS_CAT (cod_prod)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_TB_MOV_FINANCIEROS_CLIENTE_FECHA'
      AND object_id = OBJECT_ID(N'dbo.TB_MOV_FINANCIEROS')
)
BEGIN
    CREATE INDEX IX_TB_MOV_FINANCIEROS_CLIENTE_FECHA
        ON dbo.TB_MOV_FINANCIEROS (id_cli, fec_mov);
END;
GO

IF OBJECT_ID(N'dbo.TB_OBLIGACIONES', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_OBLIGACIONES
    (
        id_oblig          BIGINT         NOT NULL,
        id_cli            INT            NOT NULL,
        cod_prod          VARCHAR(10)    NOT NULL,
        vr_aprobado       DECIMAL(18, 2) NOT NULL,
        vr_desembolsado   DECIMAL(18, 2) NOT NULL,
        sdo_capital       DECIMAL(18, 2) NOT NULL,
        vr_cuota          DECIMAL(18, 2) NOT NULL,
        fec_desembolso    DATE           NOT NULL,
        fec_venc          DATE           NOT NULL,
        dias_mora_act     INT            NOT NULL,
        num_cuotas_pend   SMALLINT       NOT NULL,
        calif_riesgo      VARCHAR(5)     NULL,
        CONSTRAINT PK_TB_OBLIGACIONES PRIMARY KEY (id_oblig),
        CONSTRAINT FK_OBLIG_CLIENTE FOREIGN KEY (id_cli)
            REFERENCES dbo.TB_CLIENTES_CORE (id_cli),
        CONSTRAINT FK_OBLIG_PRODUCTO FOREIGN KEY (cod_prod)
            REFERENCES dbo.TB_PRODUCTOS_CAT (cod_prod)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_TB_OBLIGACIONES_CLIENTE'
      AND object_id = OBJECT_ID(N'dbo.TB_OBLIGACIONES')
)
BEGIN
    CREATE INDEX IX_TB_OBLIGACIONES_CLIENTE
        ON dbo.TB_OBLIGACIONES (id_cli, dias_mora_act);
END;
GO

IF OBJECT_ID(N'dbo.TB_COMISIONES_LOG', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TB_COMISIONES_LOG
    (
        id_comision    BIGINT         NOT NULL,
        id_cli         INT            NOT NULL,
        cod_prod       VARCHAR(10)    NOT NULL,
        fec_cobro      DATE           NOT NULL,
        vr_comision    DECIMAL(18, 2) NOT NULL,
        tip_comision   VARCHAR(30)    NULL,
        estado_cobro   VARCHAR(20)    NOT NULL,
        CONSTRAINT PK_TB_COMISIONES_LOG PRIMARY KEY (id_comision),
        CONSTRAINT FK_COMISION_CLIENTE FOREIGN KEY (id_cli)
            REFERENCES dbo.TB_CLIENTES_CORE (id_cli),
        CONSTRAINT FK_COMISION_PRODUCTO FOREIGN KEY (cod_prod)
            REFERENCES dbo.TB_PRODUCTOS_CAT (cod_prod)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_TB_COMISIONES_CLIENTE_FECHA'
      AND object_id = OBJECT_ID(N'dbo.TB_COMISIONES_LOG')
)
BEGIN
    CREATE INDEX IX_TB_COMISIONES_CLIENTE_FECHA
        ON dbo.TB_COMISIONES_LOG (id_cli, fec_cobro);
END;
GO