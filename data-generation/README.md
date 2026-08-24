# Generación de datos

Esta carpeta contiene los componentes necesarios para generar y cargar los datos
sintéticos del escenario bancario de FinBank.

## Contenido previsto

- configuración de volúmenes, fechas y semilla aleatoria;
- scripts de generación reproducible;
- generación en CSV y Parquet;
- anomalías intencionales documentadas;
- scripts de creación y carga de Azure SQL Database;
- pruebas de integridad y validación de conteos.

## Tablas fuente

- `TB_CLIENTES_CORE`
- `TB_PRODUCTOS_CAT`
- `TB_MOV_FINANCIEROS`
- `TB_SUCURSALES_RED`
- `TB_COMISIONES_LOG`

> Estado: pendiente de implementación.