# Evidencias de monitoreo y alertas

Esta carpeta contiene las evidencias de observabilidad de FinBank mediante Azure Monitor y Log Analytics.

| Archivo                                         | Evidencia                                                      |
| ----------------------------------------------- | -------------------------------------------------------------- |
| `01-terraform-apply-monitoreo.png`              | Despliegue de cuatro recursos de monitoreo mediante Terraform. |
| `02-terraform-plan-sin-cambios-monitoreo.png`   | Verificación de idempotencia de la infraestructura.            |
| `03-diagnosticos-alertas-azure-verificados.png` | Diagnósticos de ADF y Databricks, y alertas habilitadas.       |
| `04-action-group-email-verificado.png`          | Receptor de correo activo con esquema común.                   |
| `05-fallo-controlado-pipeline-adf.png`          | Fallo controlado en Silver–Gold para validar la alerta.        |
| `06-alerta-adf-activada.png`                    | Alerta crítica desencadenada en Azure Monitor.                 |
| `07-correo-alerta-pipeline-fallido.png`         | Notificación operacional recibida por correo.                  |
| `08-recuperacion-pipeline-exitosa.png`          | Ejecución posterior correcta del pipeline end-to-end.          |
| `09-telemetria-adf-log-analytics.png`           | Ejecuciones de ADF disponibles en Log Analytics.               |
| `10-telemetria-databricks-log-analytics.png`    | Eventos de Databricks disponibles en Log Analytics.            |

## Resultado

* Diagnósticos de ADF y Databricks enviados a Log Analytics.
* Alertas de fallos de pipelines y desencadenadores habilitadas.
* Action Group con notificación por correo validado.
* Fallo controlado detectado y notificado.
* Recuperación posterior del pipeline confirmada.
