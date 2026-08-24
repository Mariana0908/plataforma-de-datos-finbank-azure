resource "random_password" "sql_admin" {
  length           = 24
  special          = true
  override_special = "!#$%&*+-=?@_"
}

resource "azurerm_mssql_server" "main" {
  name                = "sql-${local.name_prefix}-${local.region_code}-${local.unique_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  version             = "12.0"

  administrator_login          = var.sql_admin_login
  administrator_login_password = random_password.sql_admin.result

  minimum_tls_version           = "1.2"
  public_network_access_enabled = true

  tags = local.common_tags
}

resource "azurerm_mssql_database" "main" {
  name      = "sqldb-${local.name_prefix}"
  server_id = azurerm_mssql_server.main.id

  collation                   = "SQL_Latin1_General_CP1_CI_AS"
  sku_name                    = "GP_S_Gen5_1"
  max_size_gb                 = 2
  min_capacity                = 0.5
  auto_pause_delay_in_minutes = 60
  storage_account_type        = "Local"
  zone_redundant              = false

  transparent_data_encryption_enabled = true

  tags = local.common_tags
}

resource "azurerm_mssql_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_mssql_firewall_rule" "current_client" {
  name             = "AllowCurrentClient"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = var.client_ip_address
  end_ip_address   = var.client_ip_address
}