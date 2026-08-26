# Infraestructura como código

Esta carpeta contiene la infraestructura de Microsoft Azure definida mediante Terraform.

## Recursos implementados

- Resource Group
- Azure Data Lake Storage Gen2.
- Sistemas de archivos `bronze`, `silver` y `gold`.
- Azure SQL Server
- Azure SQL Database serverless
- Storage Account con ADLS Gen2
- contenedores Bronze, Silver y Gold
- Azure Data Factory
- Azure Databricks
- Azure Databricks Access Connector con identidad administrada.
- Azure Key Vault
- Log Analytics Workspace;
- Azure Monitor Action Group.
- Identidades, políticas y asignaciones de acceso.
- Reglas de firewall para Azure SQL.

El inventario detallado se encuentra en [Inventario de recursos Azure](../docs/inventario-recursos-azure.md).


## Regiones

- Región principal: `East US`.
- Azure SQL: `Central US`.
- Action Group: `Global`.

En el caso de Azure SQL utilizará una región alternativa debido a restricciones de aprovisionamiento encontradas en East US y East US 2 para la suscripción utilizada.

## Estructura

La implementación se encuentra en [`terraform`](./terraform/).

Los archivos están separados por responsabilidad:

| Archivo | Responsabilidad |
|---|---|
| `backend.tf` | Declaración del backend remoto `azurerm`. |
| `versions.tf` | Versiones de Terraform y proveedores. |
| `providers.tf` | Configuración del proveedor de Azure. |
| `variables.tf` | Variables, tipos y validaciones. |
| `locals.tf` | Nombres, etiquetas y valores calculados. |
| `resource-group.tf` | Grupo principal de recursos. |
| `storage.tf` | Data Lake Storage Gen2 y capas Medallion. |
| `sql.tf` | Azure SQL Server, base de datos y firewall. |
| `data-factory.tf` | Azure Data Factory y permisos asociados. |
| `databricks.tf` | Workspace de Azure Databricks. |
| `databricks-access.tf` | Access Connector e identidades autorizadas para acceder a ADLS Gen2. |
| `security.tf` | Key Vault, secretos y políticas de acceso. |
| `monitoring.tf` | Log Analytics y Action Group. |
| `outputs.tf` | Nombres, FQDN y URL de los recursos. |
| `environments/` | Configuración separada de `dev` y `prod`. |
| `monitoring-diagnostics.tf` | Diagnósticos de ADF y Databricks, y alertas operacionales. |

## Requisitos

- Azure CLI autenticada.
- Terraform 1.15 o compatible.
- Permisos para administrar la suscripción.
- Rol `Storage Blob Data Contributor` sobre el almacenamiento del backend.
- Variables sensibles proporcionadas localmente.

## Variables sensibles

Los valores reales no se almacenan en el repositorio. Antes de ejecutar Terraform deben configurarse en PowerShell:

```powershell
$env:TF_VAR_subscription_id = az account show --query id --output tsv
$env:TF_VAR_client_ip_address = (Invoke-RestMethod -Uri "https://api.ipify.org").Trim()
$env:TF_VAR_alert_email = Read-Host "Correo para las alertas"
```

También puede copiarse `terraform.tfvars.example` como `terraform.tfvars`, pero este archivo local está excluido mediante `.gitignore`.

## Backend remoto

El estado de desarrollo se almacena en Azure Storage:

| Propiedad | Valor |
|---|---|
| Resource Group | `rg-finbank-tfstate-eus` |
| Storage Account | `stfinbanktf2nctv` |
| Contenedor | `tfstate` |
| Blob de desarrollo | `finbank/dev/terraform.tfstate` |
| Blob de producción | `finbank/prod/terraform.tfstate` |
| Autenticación | Microsoft Entra ID mediante Azure CLI |

El almacenamiento tiene versionado y eliminación recuperable durante siete días. No se utilizan Access Keys ni SAS Tokens en la configuración.

Los recursos del backend se crearon previamente al backend principal, porque el almacenamiento debe existir antes de ejecutar `terraform init`. Permanecen separados del estado de la plataforma para evitar que una eliminación de la solución destruya también su estado.

## Ambiente de desarrollo

```powershell
cd infra/terraform

terraform init `
    -reconfigure `
    "-backend-config=.\environments\dev.backend.hcl"

terraform fmt -recursive
terraform validate

terraform plan `
    -var-file=".\environments\dev.tfvars"

terraform apply `
    -var-file=".\environments\dev.tfvars"
```

## Ambiente de producción

La configuración está preparada, pero producción no fue desplegada como parte de esta prueba:

```powershell
terraform init `
    -reconfigure `
    "-backend-config=.\environments\prod.backend.hcl"

terraform plan `
    -var-file=".\environments\prod.tfvars"
```

No debe ejecutarse `apply` sobre producción sin una revisión y aprobación explícitas.

## Salidas

```powershell
terraform output
```

Las salidas incluyen:

- Resource Group.
- Storage Account.
- Capas Medallion.
- Azure SQL Server FQDN.
- Azure SQL Database.
- Key Vault.
- Data Factory.
- Databricks Workspace y URL.
- Databricks Access Connector: nombre, identificador y principal administrado.
- Log Analytics Workspace.
- Action Group.

## Validaciones realizadas

```powershell
terraform fmt -recursive
terraform validate
terraform plan
```

La ejecución final confirmó:

```text
No changes. Your infrastructure matches the configuration.
```
Las evidencias están disponibles en [Evidencias de infraestructura](../docs/evidencias/infraestructura/README.md).

## Acceso gobernado de Databricks a ADLS Gen2

Azure Databricks accede a las capas Bronze, Silver y Gold mediante un Access Connector con identidad administrada. No se almacenan claves de cuenta, tokens SAS ni secretos de almacenamiento en el código.

La identidad cuenta con los roles requeridos para el acceso a datos y la administración de eventos de archivos:

- `Storage Blob Data Contributor`;
- `Storage Queue Data Contributor`;
- `Storage Account Contributor`;
- `EventGrid EventSubscription Contributor`.

Unity Catalog utiliza esta identidad mediante una credencial de almacenamiento y ubicaciones externas independientes para las capas Medallion. Bronze permanece configurada como solo lectura, mientras que Silver y Gold permiten lectura y escritura.