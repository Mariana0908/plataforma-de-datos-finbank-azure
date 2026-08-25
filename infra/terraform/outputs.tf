output "resource_group_name" {
  description = "Nombre del grupo de recursos."
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Nombre de la cuenta de almacenamiento."
  value       = azurerm_storage_account.data_lake.name
}

output "medallion_filesystems" {
  description = "Contenedores de la arquitectura Medallion."
  value       = sort(keys(azurerm_storage_data_lake_gen2_filesystem.medallion))
}

output "sql_server_fqdn" {
  description = "Nombre de dominio del servidor de Azure SQL."
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  description = "Nombre de la base de datos de FinBank."
  value       = azurerm_mssql_database.main.name
}
output "key_vault_name" {
  description = "Nombre del Azure Key Vault."
  value       = azurerm_key_vault.main.name
}

output "data_factory_name" {
  description = "Nombre de Azure Data Factory."
  value       = azurerm_data_factory.main.name
}

output "databricks_workspace_name" {
  description = "Nombre del workspace de Azure Databricks."
  value       = azurerm_databricks_workspace.main.name
}

output "databricks_workspace_url" {
  description = "URL del workspace de Azure Databricks."
  value       = azurerm_databricks_workspace.main.workspace_url
}

output "log_analytics_workspace_name" {
  description = "Nombre del workspace de Log Analytics."
  value       = azurerm_log_analytics_workspace.main.name
}

output "action_group_name" {
  description = "Nombre del Action Group."
  value       = azurerm_monitor_action_group.main.name
}

output "databricks_access_connector_name" {
  description = "Nombre del Access Connector utilizado por Azure Databricks."
  value       = azurerm_databricks_access_connector.main.name
}

output "databricks_access_connector_id" {
  description = "Identificador del Access Connector utilizado por Azure Databricks."
  value       = azurerm_databricks_access_connector.main.id
}

output "databricks_access_connector_principal_id" {
  description = "Identificador de la identidad administrada del Access Connector."
  value       = azurerm_databricks_access_connector.main.identity[0].principal_id
}