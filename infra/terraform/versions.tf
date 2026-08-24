terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.2"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.9"
    }
  }
}