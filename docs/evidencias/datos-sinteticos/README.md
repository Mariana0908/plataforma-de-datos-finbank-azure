# Evidencias de generación y carga de datos sintéticos

Esta carpeta contiene evidencias reproducibles de la generación, validación y carga de las seis tablas fuente de FinBank.

## Evidencias visuales

| Archivo | Evidencia |
|---|---|
| `01-validacion-datos-completos.png` | Validación completa con 65 controles exitosos y cero fallos. |
| `02-conexion-segura-azure-sql.png` | Conexión a Azure SQL recuperando credenciales desde Key Vault. |
| `03-carga-azure-sql-exitosa.png` | Carga exitosa de 620.250 registros y código de salida cero. |
| `04-conteos-tablas-azure-sql.png` | Ejecución de conteos directamente en el Editor de consultas de Azure. |

## Evidencias estructuradas

| Archivo | Contenido |
|---|---|
| `manifest-generacion-completa.json` | Filas, columnas, formatos, hashes, semilla y anomalías introducidas. |
| `reporte-validacion-completa.json` | Resultado resumido de las validaciones automáticas. |
| `reporte-carga-azure-sql.json` | Conteos recuperados desde Azure SQL después de la carga. |
| `02-validacion-completa.txt` | Registro completo de los 65 controles ejecutados. |
| `03-carga-azure-sql.txt` | Registro de la carga por lotes en Azure SQL. |

## Resultado

| Tabla | Registros cargados |
|---|---:|
| `TB_CLIENTES_CORE` | 10.000 |
| `TB_PRODUCTOS_CAT` | 50 |
| `TB_MOV_FINANCIEROS` | 500.000 |
| `TB_OBLIGACIONES` | 30.000 |
| `TB_SUCURSALES_RED` | 200 |
| `TB_COMISIONES_LOG` | 80.000 |
| **Total** | **620.250** |

Los CSV y Parquet completos no se versionan porque pueden reproducirse mediante `data-generation/src/generate_data.py` y están excluidos en `.gitignore`.

Ninguna evidencia contiene contraseñas, tokens, claves de acceso o direcciones IP públicas.
