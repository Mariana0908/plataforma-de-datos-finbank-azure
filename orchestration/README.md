# Orquestación

Esta carpeta contiene las definiciones del pipeline principal de la orquestación end-to-end de la plataforma

## Estado
La orquestación se encuentra implementada, publicada y validada en el ambiente de desarrollo.

El flujo integra:

1. ingesta incremental Bronze mediante Azure Data Factory;
2. procesamiento Bronze → Silver mediante Azure Databricks;
3. procesamiento Silver → Gold mediante Azure Databricks;
4. ejecución secuencial, parametrizada y supervisada;
5. programación diaria mediante un desencadenador de Azure Data Factory.

## Flujo de ejecución

```text
tr_finbank_daily_dev
        |
        v
pl_finbank_end_to_end
        |
        +-- execute_bronze_ingestion
        |       |
        |       v
        |   pl_bronze_ingestion
        |
        +-- execute_silver_gold
                |
                v
        job_finbank_silver_gold_dev
                |
                +-- silver_processing
                |
                +-- gold_processing