resource "azurerm_storage_account" "data_lake" {
  name                = "dls${var.project_name}${var.environment}${local.region_code}${local.unique_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location


  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  https_traffic_only_enabled        = true
  min_tls_version                   = "TLS1_2"
  infrastructure_encryption_enabled = true
  local_user_enabled                = false
  allow_nested_items_to_be_public   = false
  public_network_access_enabled     = true

  tags = local.common_tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "medallion" {
  for_each = toset(["bronze", "silver", "gold"])

  name               = each.value
  storage_account_id = azurerm_storage_account.data_lake.id
}