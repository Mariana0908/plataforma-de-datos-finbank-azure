resource "random_string" "suffix" {
  length  = 5
  lower   = true
  numeric = true
  upper   = false
  special = false
}

locals {
  region_codes = {
    eastus    = "eus"
    eastus2   = "eus2"
    centralus = "cus"
  }

  region_code = lookup(local.region_codes, var.location, replace(var.location, " ", ""))
  sql_region_code = lookup(
    local.region_codes,
    var.sql_location,
    replace(var.sql_location, " ", "")
  )
  name_prefix   = "${var.project_name}-${var.environment}"
  unique_suffix = random_string.suffix.result

  common_tags = {
    project     = var.project_name
    environment = var.environment
    workload    = "data-platform"
    managed_by  = "terraform"
    temporary   = "true"
  }
}
