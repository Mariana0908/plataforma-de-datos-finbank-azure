resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}-${local.region_code}"
  location = var.location
  tags     = local.common_tags
}