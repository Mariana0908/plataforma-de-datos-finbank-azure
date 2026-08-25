resource "azurerm_databricks_access_connector" "main" {
  name                = "ac-dbw-${local.name_prefix}-${local.region_code}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

resource "azurerm_role_assignment" "databricks_storage" {
  scope                = azurerm_storage_account.data_lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "databricks_storage_queue" {
  scope                = azurerm_storage_account.data_lake.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_databricks_access_connector.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "databricks_storage_management" {
  scope                = azurerm_storage_account.data_lake.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_databricks_access_connector.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "databricks_eventgrid" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "EventGrid EventSubscription Contributor"
  principal_id         = azurerm_databricks_access_connector.main.identity[0].principal_id
}