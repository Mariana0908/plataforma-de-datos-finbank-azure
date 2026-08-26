# Changelog

Este archivo se utilizará para llevar un registo de los cambios significativos realizados durante el desarrollo de la plataforma de datos de FinBank.


### Added
- **2026-08-25 — Mariana Ospina Henao:** implementación y validación de CI/CD con GitHub Actions, controles automáticos de calidad y seguridad, y despliegue protegido de Terraform en `dev` mediante OIDC.
- **2026-08-25 — Mariana Ospina Henao:** implementación y validación del monitoreo operacional con Azure Monitor, Log Analytics, alertas de fallos y notificaciones por correo.
- **2026-08-25 — Mariana Ospina Henao:** implementación y validación de la orquestación end-to-end mediante Azure Data Factory y Azure Databricks, incluyendo pipeline maestro, ejecución secuencial Bronze–Silver–Gold, transferencia dinámica de parámetros, autenticación mediante identidad administrada, job de Databricks, desencadenador diario, plantillas ARM y bundle validado mediante Databricks CLI.
- **2026-08-25 — Mariana Ospina Henao:** implementación y validación de la capa Gold en Azure Databricks, incluyendo modelo dimensional, tablas de hechos, KPI bancarios, marts analíticos, controles de integridad, minimización de datos personales, conciliación Silver–Gold e idempotencia.
- **2026-08-24 — Mariana Ospina Henao:** definición de GitHub Flow como estrategia de versionamiento, incluyendo convenciones para ramas, commits y Pull Requests.
- **2026-08-23 — Mariana Ospina Henao:** creación del repositorio público `plataforma-de-datos-finbank-azure`.
- **2026-08-23 — Mariana Ospina Henao:** creación de la estructura principal: `infra`,`data-generation`, `pipelines`, `orchestration` y `docs`.
- **2026-08-23 — Mariana Ospina Henao:** incorporación del `.gitignore` para proteger estados de Terraform, credenciales, entornos virtuales, archivos temporales y datos generados.
- **2026-08-23 — Mariana Ospina Henao:** creación del README inicial con el escenario bancario seleccionado, la plataforma Azure, la elección de Terraform, el alcance técnico y el estado de implementación.

### Changed

- Sin cambios registrados.

### Fixed

- Sin correcciones registradas.

### Security

- **2026-08-23 — Mariana Ospina Henao:** exclusión preventiva de credenciales,
  secretos, configuraciones locales de Azure y Databricks, certificados y archivos
  de estado de Terraform.