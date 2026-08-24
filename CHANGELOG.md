# Changelog

Este archivo registra los cambios significativos realizados durante el desarrollo de
la plataforma de datos de FinBank.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto utilizará versionamiento semántico cuando se generen versiones
formales.

## [Unreleased]

### Added

- **2026-08-23 — Mariana Ospina Henao:** creación del repositorio público
  `plataforma-de-datos-finbank-azure`.
- **2026-08-23 — Mariana Ospina Henao:** creación de la estructura principal:
  `infra`, `data-generation`, `pipelines`, `orchestration` y `docs`.
- **2026-08-23 — Mariana Ospina Henao:** incorporación del `.gitignore` para
  proteger estados de Terraform, credenciales, entornos virtuales, archivos
  temporales y datos generados.
- **2026-08-23 — Mariana Ospina Henao:** creación del README inicial con el
  escenario bancario seleccionado, la plataforma Azure, la elección de Terraform,
  el alcance técnico y el estado de implementación.

### Changed

- Sin cambios registrados.

### Fixed

- Sin correcciones registradas.

### Security

- **2026-08-23 — Mariana Ospina Henao:** exclusión preventiva de credenciales,
  secretos, configuraciones locales de Azure y Databricks, certificados y archivos
  de estado de Terraform.