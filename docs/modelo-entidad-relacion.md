# Modelo entidad-relación de las tablas fuente

Este modelo representa las seis estructuras del sistema transaccional de FinBank utilizadas para generar y cargar los datos sintéticos.

```mermaid
erDiagram
    TB_CLIENTES_CORE ||--o{ TB_MOV_FINANCIEROS : realiza
    TB_CLIENTES_CORE ||--o{ TB_OBLIGACIONES : posee
    TB_CLIENTES_CORE ||--o{ TB_COMISIONES_LOG : paga
    TB_PRODUCTOS_CAT ||--o{ TB_MOV_FINANCIEROS : clasifica
    TB_PRODUCTOS_CAT ||--o{ TB_OBLIGACIONES : define
    TB_PRODUCTOS_CAT ||--o{ TB_COMISIONES_LOG : origina

    TB_CLIENTES_CORE {
        int id_cli PK
        string nomb_cli
        string apell_cli
        string tip_doc
        string num_doc
        date fec_nac
        date fec_alta
        string cod_segmento
        int score_buro
        string ciudad_res
        string depto_res
        string estado_cli
        string canal_adquis
    }

    TB_PRODUCTOS_CAT {
        string cod_prod PK
        string desc_prod
        string tip_prod
        decimal tasa_ea
        int plazo_max_meses
        decimal cuota_min
        decimal comision_admin
        string estado_prod
    }

    TB_MOV_FINANCIEROS {
        long id_mov
        int id_cli FK
        string cod_prod FK
        string num_cuenta
        date fec_mov
        time hra_mov
        decimal vr_mov
        string tip_mov
        string cod_canal
        string cod_ciudad
        string cod_estado_mov
        string id_dispositivo
    }

    TB_OBLIGACIONES {
        long id_oblig PK
        int id_cli FK
        string cod_prod FK
        decimal vr_aprobado
        decimal vr_desembolsado
        decimal sdo_capital
        decimal vr_cuota
        date fec_desembolso
        date fec_venc
        int dias_mora_act
        int num_cuotas_pend
        string calif_riesgo
    }

    TB_SUCURSALES_RED {
        string cod_suc PK
        string nom_suc
        string tip_punto
        string ciudad
        string depto
        decimal latitud
        decimal longitud
        boolean activo
    }

    TB_COMISIONES_LOG {
        long id_comision PK
        int id_cli FK
        string cod_prod FK
        date fec_cobro
        decimal vr_comision
        string tip_comision
        string estado_cobro
    }
```

## Relaciones

- Un cliente puede tener múltiples movimientos, obligaciones y comisiones.
- Un producto puede aparecer en múltiples movimientos, obligaciones y comisiones.
- `TB_SUCURSALES_RED` funciona como catálogo geográfico de puntos de atención.
- La fuente no proporciona `cod_suc` en `TB_MOV_FINANCIEROS`; por tanto, no se inventa una llave foránea entre ambas tablas. Su integración analítica se realizará por ciudad y reglas de homologación en Silver.
- `id_mov` no se declara como llave primaria física en Azure SQL porque el conjunto sintético incluye duplicados intencionales que deben llegar a Bronze para ser detectados.

## Datos sensibles

`num_doc`, nombres y apellidos se consideran datos sensibles aunque sean sintéticos. En Silver se aplicará enmascaramiento o tokenización antes de exponerlos a consumidores analíticos.
