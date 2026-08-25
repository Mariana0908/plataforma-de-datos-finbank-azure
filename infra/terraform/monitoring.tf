resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}-${local.region_code}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  sku               = "PerGB2018"
  retention_in_days = 30
  daily_quota_gb    = 0.1

  tags = local.common_tags
}

resource "azurerm_monitor_action_group" "main" {
  name                = "ag-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "finbankdev"

  email_receiver {
    name                    = "platform-owner"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  tags = local.common_tags
}