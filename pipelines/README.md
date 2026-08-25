# Pipelines de datos

Esta carpeta contiene el código de ingesta y procesamiento de la arquitectura Medallion.

## Capas

- [Bronze] (./bronze/README.md): ingesta incremental desde Azure SQL Database hacia ADLS Gen2.
- Silver: limpieza, validación y estandarización de datos.
- Gold:  construcción de indicadores y modelos analíticos.

## Estado

- Bronze: implementada y validada.
- Silver: pendiente de implementación.
- Gold: pendiente de implementación.