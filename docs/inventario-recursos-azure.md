# Inventario de recursos de Azure

Este documento registra los recursos desplegados para la plataforma de datos de FinBank.

## Plataforma de datos

| Recurso | Tipo | Región | Propósito |
|---|---|---|---|
| `rg-finbank-dev-eus` | Resource Group | East US | Agrupar y administrar la plataforma de desarrollo. |
| `dlsfinbankdeveus2nctv` | ADLS Gen2 | East US | Almacenar datos en las capas Bronze, Silver y Gold. |
| `adf-finbank-dev-eus-2nctv` | Azure Data Factory | East US | Orquestar la ingesta y ejecución de procesos. |
| `dbw-finbank-dev-eus` | Azure Databricks | East US | Ejecutar transformaciones con Spark y PySpark. |
| `kv-finbank-dev-2nctv` | Azure Key Vault | East US | Proteger las credenciales de Azure SQL. |
| `log-finbank-dev-eus` | Log Analytics Workspace | East US | Centralizar registros y telemetría operativa. |
| `ag-finbank-dev` | Action Group | Global | Enviar notificaciones operativas. |
| `sql-finbank-dev-cus-2nctv` | Azure SQL Server | Central US | Alojar el sistema fuente sintético de FinBank. |
| `sqldb-finbank-dev` | Azure SQL Database | Central US | Almacenar las seis tablas fuente del escenario bancario. |

Azure crea automáticamente la base `master` dentro del servidor SQL. Esta base no contiene información funcional de FinBank y no se administra como una base separada mediante Terraform.

## Capas del Data Lake

| Sistema de archivos | Propósito |
|---|---|
| `bronze` | Datos ingeridos sin transformaciones funcionales. |
| `silver` | Datos depurados, tipificados y validados. |
| `gold` | Datos agregados y preparados para indicadores. |

## Backend de Terraform

| Recurso | Tipo | Región | Propósito |
|---|---|---|---|
| `rg-finbank-tfstate-eus` | Resource Group | East US | Aislar los recursos del backend. |
| `stfinbanktf2nctv` | Azure Storage | East US | Almacenar el estado remoto versionado. |
| `tfstate` | Blob Container | East US | Contener los estados separados por ambiente. |
| `finbank/dev/terraform.tfstate` | Block Blob | East US | Estado remoto del ambiente de desarrollo. |

El backend utiliza Microsoft Entra ID, bloqueo del estado, versionado y eliminación recuperable durante siete días.

## Regiones

La región principal es `East US`. Azure SQL fue desplegado en `Central US` debido a restricciones de aprovisionamiento presentadas por la suscripción en `East US` y `East US 2`.

## Administración mediante Terraform

El estado contiene:

- 21 recursos administrados.
- 1 fuente de datos para consultar la identidad activa de Azure.
- 22 direcciones totales en `terraform state list`.

La última validación confirmó que la infraestructura real coincide con la configuración.