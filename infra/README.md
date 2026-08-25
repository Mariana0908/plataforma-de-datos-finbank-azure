# Infraestructura como código

Esta carpeta contiene la infraestructura de Microsoft Azure definida mediante Terraform.

## Recursos previstos

- Resource Group;
- Azure SQL Server
- Azure SQL Database serverless;
- Storage Account con ADLS Gen2;
- contenedores Bronze, Silver y Gold;
- Azure Data Factory;
- Azure Databricks;
- Azure Key Vault;
- Log Analytics Workspace;
- Action Group;
- Identidades, políticas y asignaciones de acceso.

## Regiones

- Región principal: `East US`.
- Azure SQL: `Central US`.

En el caso de Azure SQL utilizará una región alternativa debido a restricciones de aprovisionamiento encontradas en East US y East US 2 para la suscripción utilizada.

## Estructura

La implementación se encuentra en [`terraform`](./terraform/).

Los archivos están separados por responsabilidad:
- Proveedores y versiones.
- Variables y valores locales.
- Recursos de almacenamiento.
- Azure SQL.
- Azure Data Factory.
- Azure Databricks.
- Seguridad.
- Monitoreo.
- Salidas.

## Ejecución

```powershell
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
