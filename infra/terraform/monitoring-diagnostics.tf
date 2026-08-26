resource "azurerm_monitor_diagnostic_setting" "data_factory" {
  name                       = "diag-adf-${local.name_prefix}"
  target_resource_id         = azurerm_data_factory.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  log_analytics_destination_type = "Dedicated"

  enabled_log {
    category = "ActivityRuns"
  }

  enabled_log {
    category = "PipelineRuns"
  }

  enabled_log {
    category = "TriggerRuns"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

resource "azurerm_monitor_diagnostic_setting" "databricks" {
  name                       = "diag-dbw-${local.name_prefix}"
  target_resource_id         = azurerm_databricks_workspace.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "jobs"
  }

  enabled_log {
    category = "notebook"
  }

  enabled_log {
    category = "workspace"
  }

  enabled_log {
    category = "unityCatalog"
  }

  enabled_log {
    category = "RBAC"
  }

  enabled_log {
    category = "secrets"
  }
}

resource "azurerm_monitor_metric_alert" "data_factory_pipeline_failed" {
  name                = "alert-adf-pipeline-failed-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_data_factory.main.id]
  description         = "Alerta cuando uno o más pipelines de Azure Data Factory finalizan con error."

  severity      = 1
  enabled       = true
  auto_mitigate = true
  frequency     = "PT1M"
  window_size   = "PT5M"

  criteria {
    metric_namespace = "Microsoft.DataFactory/factories"
    metric_name      = "PipelineFailedRuns"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = local.common_tags
}

resource "azurerm_monitor_metric_alert" "data_factory_trigger_failed" {
  name                = "alert-adf-trigger-failed-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_data_factory.main.id]
  description         = "Alerta cuando uno o más desencadenadores de Azure Data Factory finalizan con error."

  severity      = 2
  enabled       = true
  auto_mitigate = true
  frequency     = "PT1M"
  window_size   = "PT5M"

  criteria {
    metric_namespace = "Microsoft.DataFactory/factories"
    metric_name      = "TriggerFailedRuns"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = local.common_tags
}