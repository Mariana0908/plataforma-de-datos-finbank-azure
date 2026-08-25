"""Crea y carga las tablas fuente de FinBank en Azure SQL Database."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyodbc
from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient


LOGGER = logging.getLogger("finbank-sql-loader")
SCRIPT_PATH = Path(__file__).resolve()

LOAD_ORDER = [
    "TB_CLIENTES_CORE",
    "TB_PRODUCTOS_CAT",
    "TB_SUCURSALES_RED",
    "TB_OBLIGACIONES",
    "TB_MOV_FINANCIEROS",
    "TB_COMISIONES_LOG",
]

DELETE_ORDER = [
    "TB_COMISIONES_LOG",
    "TB_MOV_FINANCIEROS",
    "TB_OBLIGACIONES",
    "TB_SUCURSALES_RED",
    "TB_PRODUCTOS_CAT",
    "TB_CLIENTES_CORE",
]

DATE_COLUMNS = {
    "TB_CLIENTES_CORE": ["fec_nac", "fec_alta"],
    "TB_MOV_FINANCIEROS": ["fec_mov"],
    "TB_OBLIGACIONES": ["fec_desembolso", "fec_venc"],
    "TB_COMISIONES_LOG": ["fec_cobro"],
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, help="FQDN del servidor de Azure SQL.")
    parser.add_argument("--database", required=True, help="Nombre de Azure SQL Database.")
    parser.add_argument("--key-vault", required=True, help="Nombre de Azure Key Vault.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=SCRIPT_PATH.parents[1] / "output" / "parquet",
        help="Carpeta que contiene los archivos Parquet.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=SCRIPT_PATH.parents[1] / "sql" / "create_tables.sql",
        help="Script SQL de creación de tablas.",
    )
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Elimina los registros existentes antes de cargar.",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Comprueba Key Vault y Azure SQL sin crear ni cargar tablas.",
    )
    return parser.parse_args()


def get_sql_credentials(key_vault_name: str) -> tuple[str, str]:
    credential = AzureCliCredential()
    client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net",
        credential=credential,
    )
    LOGGER.info("Recuperando credenciales desde Azure Key Vault")
    username = client.get_secret("sql-admin-login").value
    password = client.get_secret("sql-admin-password").value
    if not username or not password:
        raise RuntimeError("Key Vault devolvió credenciales SQL vacías.")
    return username, password


def connect_with_retry(
    server: str,
    database: str,
    username: str,
    password: str,
    attempts: int = 4,
) -> pyodbc.Connection:
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )
    for attempt in range(1, attempts + 1):
        try:
            LOGGER.info("Conectando a Azure SQL (intento %s/%s)", attempt, attempts)
            return pyodbc.connect(connection_string, autocommit=False)
        except pyodbc.Error:
            if attempt == attempts:
                raise
            LOGGER.warning("Azure SQL aún no responde; nuevo intento en 15 segundos")
            time.sleep(15)
    raise RuntimeError("No fue posible establecer la conexión.")


def execute_schema(connection: pyodbc.Connection, schema_path: Path) -> None:
    sql_text = schema_path.read_text(encoding="utf-8")
    batches = re.split(r"^\s*GO\s*$", sql_text, flags=re.MULTILINE | re.IGNORECASE)
    cursor = connection.cursor()
    try:
        for batch in batches:
            if batch.strip():
                cursor.execute(batch)
        connection.commit()
        LOGGER.info("Esquema SQL creado o verificado")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def delete_existing_rows(connection: pyodbc.Connection) -> None:
    cursor = connection.cursor()
    try:
        for table_name in DELETE_ORDER:
            cursor.execute(f"DELETE FROM dbo.[{table_name}];")
        connection.commit()
        LOGGER.info("Registros anteriores eliminados en orden referencial")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def normalize_batch(frame: pd.DataFrame, table_name: str) -> pd.DataFrame:
    normalized = frame.copy()
    for column in DATE_COLUMNS.get(table_name, []):
        normalized[column] = pd.to_datetime(normalized[column]).dt.date
    normalized = normalized.astype(object).where(pd.notna(normalized), None)
    return normalized


def insert_table(
    connection: pyodbc.Connection,
    table_name: str,
    parquet_path: Path,
    batch_size: int,
) -> int:
    frame = pd.read_parquet(parquet_path)
    columns = list(frame.columns)
    column_sql = ", ".join(f"[{column}]" for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = f"INSERT INTO dbo.[{table_name}] ({column_sql}) VALUES ({placeholders});"

    cursor = connection.cursor()
    cursor.fast_executemany = True
    inserted = 0
    try:
        for start in range(0, len(frame), batch_size):
            batch = normalize_batch(frame.iloc[start : start + batch_size], table_name)
            rows = list(batch.itertuples(index=False, name=None))
            cursor.executemany(insert_sql, rows)
            connection.commit()
            inserted += len(rows)
            LOGGER.info(
                "%s: %s/%s registros cargados",
                table_name,
                f"{inserted:,}",
                f"{len(frame):,}",
            )
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def query_counts(connection: pyodbc.Connection) -> dict[str, int]:
    cursor = connection.cursor()
    counts: dict[str, int] = {}
    try:
        for table_name in LOAD_ORDER:
            cursor.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{table_name}];")
            counts[table_name] = int(cursor.fetchone()[0])
        return counts
    finally:
        cursor.close()


def validate_inputs(input_dir: Path, schema_path: Path) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"No existe el script SQL: {schema_path}")
    missing = [
        str(input_dir / f"{table_name}.parquet")
        for table_name in LOAD_ORDER
        if not (input_dir / f"{table_name}.parquet").exists()
    ]
    if missing:
        raise FileNotFoundError(f"Faltan archivos Parquet: {missing}")


def write_report(counts: dict[str, int], output_path: Path, args: argparse.Namespace) -> None:
    report: dict[str, Any] = {
        "status": "SUCCESS",
        "server": args.server,
        "database": args.database,
        "authentication": "Azure Key Vault",
        "tables": counts,
        "total_rows": sum(counts.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    logging.getLogger(
        "azure.core.pipeline.policies.http_logging_policy"
    ).setLevel(logging.WARNING)

    args = parse_arguments()
    input_dir = args.input_dir.resolve()
    schema_path = args.schema_file.resolve()
    validate_inputs(input_dir, schema_path)

    username, password = get_sql_credentials(args.key_vault)
    connection = connect_with_retry(args.server, args.database, username, password)
    try:
        if args.test_connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT DB_NAME(), SUSER_SNAME();")
                database_name, login_name = cursor.fetchone()
                print("CONEXIÓN A AZURE SQL: SUCCESS")
                print(f"BASE DE DATOS: {database_name}")
                print(f"USUARIO: {login_name}")
                return
            finally:
                cursor.close()

        execute_schema(connection, schema_path)
        if args.replace:
            delete_existing_rows(connection)

        loaded_counts: dict[str, int] = {}
        for table_name in LOAD_ORDER:
            parquet_path = input_dir / f"{table_name}.parquet"
            loaded_counts[table_name] = insert_table(
                connection, table_name, parquet_path, args.batch_size
            )

        database_counts = query_counts(connection)
        if database_counts != loaded_counts:
            raise RuntimeError(
                f"Los conteos de Azure SQL no coinciden con la carga: {database_counts}"
            )

        report_path = SCRIPT_PATH.parents[1] / "output" / "sql-load-report.json"
        write_report(database_counts, report_path, args)
        print("\n" + "=" * 72)
        print("CARGA A AZURE SQL: SUCCESS")
        for table_name, count in database_counts.items():
            print(f"{table_name}: {count:,}")
        print(f"TOTAL: {sum(database_counts.values()):,}")
        print(f"REPORTE: {report_path}")
        print("=" * 72)
    finally:
        connection.close()


if __name__ == "__main__":
    main()