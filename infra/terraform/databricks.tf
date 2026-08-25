resource "azurerm_databricks_workspace" "main" {
  name                        = "dbw-${local.name_prefix}-${local.region_code}"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = azurerm_resource_group.main.location
  sku                         = "premium"
  managed_resource_group_name = "rg-dbw-${local.name_prefix}-${local.region_code}-${local.unique_suffix}"

  public_network_access_enabled = true

  tags = local.common_tags
}