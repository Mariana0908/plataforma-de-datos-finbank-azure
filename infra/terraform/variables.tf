variable "subscription_id" {
  description = "Identificador de la suscripción de Azure."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Nombre corto del proyecto."
  type        = string
  default     = "finbank"

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.project_name))
    error_message = "El nombre del proyecto solo puede contener letras minúsculas y números."
  }
}

variable "environment" {
  description = "Ambiente de despliegue."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "El ambiente debe ser dev o prod."
  }
}

variable "location" {
  description = "Región principal de Azure."
  type        = string
  default     = "eastus"
}

variable "sql_admin_login" {
  description = "Nombre del administrador de Azure SQL."
  type        = string
  default     = "finbankadmin"
}

variable "client_ip_address" {
  description = "Dirección IPv4 autorizada temporalmente para acceder a Azure SQL."
  type        = string
  sensitive   = true

  validation {
    condition     = can(cidrhost("${var.client_ip_address}/32", 0))
    error_message = "La dirección proporcionada debe ser una IPv4 válida."
  }
}

variable "alert_email" {
  description = "Correo que recibirá las alertas operativas."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "Debe proporcionar una dirección de correo válida."
  }
}