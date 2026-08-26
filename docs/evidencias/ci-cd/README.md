# Evidencias de CI/CD

Esta carpeta documenta la automatización de validaciones y del despliegue de infraestructura del ambiente `dev`.

| Archivo | Evidencia |
|---|---|
| `01-checks-integracion-continua-exitosos.png` | Validaciones exitosas de Python, JSON, YAML, Terraform y detección de secretos. |
| `02-entorno-dev-protegido.png` | Entorno `dev` restringido a `main` y protegido mediante aprobación. |
| `03-acceso-key-vault-cd-aplicado.png` | Acceso controlado de la identidad de GitHub Actions a Azure Key Vault. |
| `04-apply-cd-dev-exitoso.png` | Ejecución de Terraform mediante OIDC con resultado `0 added, 0 changed, 0 destroyed`. |

## Resultado

- CI ejecutado automáticamente en Pull Requests.
- CD manual y protegido para el ambiente `dev`.
- Autenticación OIDC sin secretos permanentes.
- Estado remoto de Terraform en Azure Storage.
- Validación y despliegue reproducibles desde GitHub Actions.