# Pipelines de datos

Esta carpeta contiene el código de ingesta y procesamiento de la arquitectura Medallion.

## Capas

- [Bronze](./bronze/README.md): ingesta incremental desde Azure SQL Database hacia ADLS Gen2.
- [Silver](./silver/README.md): limpieza, validación, deduplicación y estandarización de datos mediante Azure Databricks.
- [Gold](./gold/README.md): modelo dimensional, indicadores bancarios y objetos analíticos mediante Azure Databricks y Delta Lake.

## Estado

- Bronze: implementada y validada.
- Silver: implementada y validada.
- Gold: implementada y validada.

Las tres capas de la arquitectura Medallion se encuentran operativas y cuentan con código, documentación y evidencias reproducibles.