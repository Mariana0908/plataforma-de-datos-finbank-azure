# Evidencias de la orquestación end-to-end

Esta carpeta contiene las evidencias de configuración, seguridad, validación y ejecución del flujo end-to-end de FinBank mediante Azure Data Factory y Azure Databricks.

| Archivo | Evidencia |
|---|---|
| `01-identidad-adf-registrada-databricks.png` | Identidad administrada de Azure Data Factory registrada como entidad de servicio en Databricks. |
| `02-job-databricks-silver-gold-configurado.png` | Job de Databricks con las tareas Silver y Gold configuradas secuencialmente. |
| `03-permiso-adf-ejecucion-job.png` | Permiso `Can Manage Run` concedido a la identidad de ADF sobre el job. |
| `04-job-databricks-ejecucion-exitosa.png` | Ejecución manual exitosa de las tareas Silver y Gold. |
| `05-acceso-adf-databricks-verificado.png` | Verificación del acceso de la identidad administrada de ADF al workspace. |
| `06-servicio-vinculado-databricks-adf.png` | Servicio vinculado de Azure Databricks autenticado mediante identidad administrada. |
| `07-pipeline-end-to-end-validado.png` | Pipeline maestro, parámetros y dependencias validados sin errores. |
| `08-ejecucion-end-to-end-depuracion-exitosa.png` | Ejecución de depuración completa con Bronze y el job Silver–Gold exitosos. |
| `09-ejecucion-publicada-end-to-end.png` | Ejecución del pipeline publicado desde el monitor de Azure Data Factory. |
| `10-actividades-end-to-end-exitosas.png` | Detalle de las actividades Bronze y Silver–Gold finalizadas correctamente. |
| `11-desencadenador-diario-configurado.png` | Desencadenador diario configurado y detenido intencionalmente en desarrollo. |
| `12-bundle-databricks-validado.png` | Definición reproducible del job validada mediante Databricks CLI con código de salida `0`. |

## Resultado consolidado

- Pipeline maestro publicado y validado.
- Bronze, Silver y Gold ejecutados secuencialmente.
- Identidad administrada utilizada sin tokens personales.
- Parámetros transferidos dinámicamente.
- Dependencias de éxito verificadas.
- Ejecución de depuración exitosa.
- Ejecución publicada exitosa.
- Desencadenador diario configurado.
- Plantillas ARM exportadas y verificadas.
- Bundle de Databricks validado correctamente.

El desencadenador permanece detenido en desarrollo para controlar costos y evitar ejecuciones automáticas involuntarias.

Las capturas excluyen credenciales, tokens, correos e identificadores sensibles.