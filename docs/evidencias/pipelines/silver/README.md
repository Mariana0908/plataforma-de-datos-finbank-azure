# Evidencias del procesamiento Silver

Esta carpeta contiene las evidencias de acceso gobernado a ADLS Gen2,
configuración de Unity Catalog, ejecución del notebook y validación de las
tablas Delta Silver de FinBank.

| Archivo | Evidencia |
|---|---|
| `01-access-connector-terraform.png` | Creación del Access Connector mediante Terraform. |
| `02-acceso-databricks-adls-verificado.png` | Asignación de acceso entre Databricks y ADLS Gen2. |
| `03-access-connector-azure.png` | Access Connector desplegado en Azure. |
| `04-unity-catalog-habilitado.png` | Unity Catalog disponible en el workspace. |
| `05-credencial-almacenamiento-databricks.png` | Credencial administrada de almacenamiento. |
| `06-permisos-eventos-databricks.png` | Permisos requeridos para eventos de archivos. |
| `07-bronze-solo-lectura-validado.png` | Acceso de solo lectura validado para Bronze. |
| `08-ubicacion-silver-validada.png` | Acceso de lectura y escritura validado para Silver. |
| `09-ubicacion-gold-validada.png` | Acceso de lectura y escritura validado para Gold. |
| `10-ubicaciones-externas-medallion.png` | Ubicaciones externas de la arquitectura Medallion. |
| `11-esquemas-unity-catalog.png` | Esquemas Bronze, Silver, Quality y Gold. |
| `12-volumenes-unity-catalog.png` | Volúmenes externos registrados. |
| `13-directorios-bronze-desde-databricks.png` | Lectura de los seis directorios Bronze. |
| `14-procesamiento-bronze-silver-exitoso.png` | Ejecución del notebook y reglas de calidad. |
| `15-conteos-tablas-delta-silver.png` | Conteos finales de las seis tablas Delta. |
| `16-calidad-movimientos-silver.png` | Deduplicación, estandarización e indicador sospechoso. |
| `17-integridad-referencial-silver.png` | Validaciones relacionales con resultado cero. |
| `18-idempotencia-procesamiento-silver.png` | Dos ejecuciones con resultados estables. |

## Resultado consolidado

- seis tablas Delta publicadas;
- 620.252 registros leídos desde Bronze;
- 618.751 registros canónicos publicados en Silver;
- 3.999 registros enviados a cuarentena;
- 498.501 movimientos con identificadores únicos;
- cero registros huérfanos en las relaciones evaluadas;
- dos ejecuciones consecutivas con los mismos conteos.

Los identificadores técnicos de ejecución no constituyen credenciales. Las
capturas excluyen claves, tokens, correos e identificadores de suscripción.
