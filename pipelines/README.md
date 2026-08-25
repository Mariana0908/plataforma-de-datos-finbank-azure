# Pipelines de datos

Esta carpeta contiene el código de ingesta y procesamiento de la arquitectura Medallion.

## Capas

- [Bronze](./bronze/README.md): ingesta incremental desde Azure SQL Database hacia ADLS Gen2.
- [Silver](./silver/README.md): limpieza, validación, deduplicación y estandarización de datos mediante Azure DAtabricks.
- Gold:  construcción de indicadores y modelos analíticos.

## Estado

- Bronze: implementada y validada.
- Silver: implementada y validada.
- Gold: pendiente de implementación.