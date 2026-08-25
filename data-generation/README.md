# Generación y carga de datos sintéticos

Esta carpeta contiene los componentes reproducibles para generar, validar y cargar en Azure SQL Database las tablas fuente del escenario bancario de FinBank.

## Tablas y volúmenes

| Tabla | Volumen mínimo |
|---|---:|
| `TB_CLIENTES_CORE` | 10.000 |
| `TB_PRODUCTOS_CAT` | 50 |
| `TB_MOV_FINANCIEROS` | 500.000 |
| `TB_OBLIGACIONES` | 30.000 |
| `TB_SUCURSALES_RED` | 200 |
| `TB_COMISIONES_LOG` | 80.000 |

Total cargado en Azure SQL: **620.250 registros**.

Los datos cubren desde el 1 de agosto de 2025 hasta el 24 de agosto de 2026 y se generan en CSV y Parquet.

## Estructura

```text
data-generation/
├── config/
│   └── generation.yaml
├── sql/
│   ├── create_tables.sql
│   └── validate_counts.sql
├── src/
│   ├── generate_data.py
│   ├── load_to_sql.py
│   └── validate_data.py
├── tests/
├── ANOMALIAS.md
├── requirements.txt
└── requirements-lock.txt
```

Los archivos generados se escriben en `output/`. Esta carpeta no se versiona porque contiene artefactos reproducibles y de gran tamaño.

## Configuración

`config/generation.yaml` centraliza:

- semilla aleatoria fija;
- fecha inicial y final;
- porcentaje de nulos;
- volumen por tabla;
- formatos de salida;
- patrones y porcentajes de anomalías.

La semilla configurada es `20260825`, lo que permite repetir la generación con los mismos resultados.

## Preparación del entorno

Desde la raíz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\data-generation\requirements-lock.txt
```

`requirements.txt` registra las dependencias directas y `requirements-lock.txt` conserva las versiones exactas utilizadas.

## Prueba rápida

Antes de generar el volumen completo se puede ejecutar una prueba reducida:

```powershell
python .\data-generation\src\generate_data.py --smoke-test
python .\data-generation\src\validate_data.py --smoke-test
```

El smoke test escribe sus resultados en `data-generation/output/smoke/`.

## Generación y validación completa

```powershell
python .\data-generation\src\generate_data.py
python .\data-generation\src\validate_data.py
```

El validador comprueba:

- archivos CSV y Parquet;
- volúmenes mínimos;
- estructuras y nombres exactos;
- hashes SHA-256;
- llaves primarias e integridad referencial;
- aproximadamente 5 % de nulos en campos no críticos;
- anomalías intencionales;
- consistencia de montos y fechas.

La ejecución completa superó 65 controles sin fallos.

## Carga en Azure SQL

Los nombres de los recursos se obtienen desde Terraform:

```powershell
Push-Location .\infra\terraform
$sqlServer = terraform output -raw sql_server_fqdn
$sqlDatabase = terraform output -raw sql_database_name
$keyVault = terraform output -raw key_vault_name
Pop-Location
```

Prueba de conexión sin modificar datos:

```powershell
python .\data-generation\src\load_to_sql.py `
    --server $sqlServer `
    --database $sqlDatabase `
    --key-vault $keyVault `
    --test-connection
```

Carga reproducible:

```powershell
python .\data-generation\src\load_to_sql.py `
    --server $sqlServer `
    --database $sqlDatabase `
    --key-vault $keyVault `
    --replace
```

El cargador recupera el usuario y la contraseña desde Azure Key Vault mediante `AzureCliCredential`. Ninguna credencial se almacena en código, configuración o evidencias.

`--replace` elimina únicamente los registros previos de las seis tablas dentro de la base dedicada y vuelve a cargarlos respetando el orden de las relaciones.

## Validación en Azure SQL

`sql/validate_counts.sql` consulta directamente el número de registros cargados. La validación final obtuvo:

```text
TB_CLIENTES_CORE      10.000
TB_PRODUCTOS_CAT          50
TB_MOV_FINANCIEROS   500.000
TB_OBLIGACIONES       30.000
TB_SUCURSALES_RED        200
TB_COMISIONES_LOG     80.000
```

## Documentación relacionada

- [Anomalías intencionales](./ANOMALIAS.md)
- [Modelo entidad-relación](../docs/modelo-entidad-relacion.md)
- [Evidencias de datos sintéticos](../docs/evidencias/datos-sinteticos/README.md)

> Estado: generación, validación y carga relacional implementadas.
