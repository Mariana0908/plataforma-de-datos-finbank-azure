"""Para validar los datos sintéticos generados para FinBank."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import yaml


SCRIPT_PATH = Path(__file__).resolve()

EXPECTED_COLUMNS = {
    "TB_CLIENTES_CORE": [
        "id_cli", "nomb_cli", "apell_cli", "tip_doc", "num_doc", "fec_nac",
        "fec_alta", "cod_segmento", "score_buro", "ciudad_res", "depto_res",
        "estado_cli", "canal_adquis",
    ],
    "TB_PRODUCTOS_CAT": [
        "cod_prod", "desc_prod", "tip_prod", "tasa_ea", "plazo_max_meses",
        "cuota_min", "comision_admin", "estado_prod",
    ],
    "TB_MOV_FINANCIEROS": [
        "id_mov", "id_cli", "cod_prod", "num_cuenta", "fec_mov", "hra_mov",
        "vr_mov", "tip_mov", "cod_canal", "cod_ciudad", "cod_estado_mov",
        "id_dispositivo",
    ],
    "TB_OBLIGACIONES": [
        "id_oblig", "id_cli", "cod_prod", "vr_aprobado", "vr_desembolsado",
        "sdo_capital", "vr_cuota", "fec_desembolso", "fec_venc",
        "dias_mora_act", "num_cuotas_pend", "calif_riesgo",
    ],
    "TB_SUCURSALES_RED": [
        "cod_suc", "nom_suc", "tip_punto", "ciudad", "depto", "latitud",
        "longitud", "activo",
    ],
    "TB_COMISIONES_LOG": [
        "id_comision", "id_cli", "cod_prod", "fec_cobro", "vr_comision",
        "tip_comision", "estado_cobro",
    ],
}

PRIMARY_KEYS = {
    "TB_CLIENTES_CORE": "id_cli",
    "TB_PRODUCTOS_CAT": "cod_prod",
    "TB_OBLIGACIONES": "id_oblig",
    "TB_SUCURSALES_RED": "cod_suc",
    "TB_COMISIONES_LOG": "id_comision",
}

NULLABLE_COLUMNS = {
    "TB_CLIENTES_CORE": ["score_buro", "canal_adquis"],
    "TB_MOV_FINANCIEROS": ["id_dispositivo"],
    "TB_OBLIGACIONES": ["calif_riesgo"],
    "TB_COMISIONES_LOG": ["tip_comision"],
}

SMOKE_VOLUMES = {
    "TB_CLIENTES_CORE": 100,
    "TB_PRODUCTOS_CAT": 10,
    "TB_MOV_FINANCIEROS": 2_000,
    "TB_OBLIGACIONES": 300,
    "TB_SUCURSALES_RED": 20,
    "TB_COMISIONES_LOG": 500,
}


class ValidationReport:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def check(self, condition: bool, success: str, failure: str) -> None:
        if condition:
            self.passed.append(success)
            print(f"[OK] {success}")
        else:
            self.failed.append(failure)
            print(f"[ERROR] {failure}")

    @property
    def is_valid(self) -> bool:
        return not self.failed


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=SCRIPT_PATH.parents[1] / "config" / "generation.yaml",
        help="Ruta del archivo YAML de configuración.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Valida los datos ubicados en output/smoke.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("rb") as file:
        return max(sum(block.count(b"\n") for block in iter(lambda: file.read(1024 * 1024), b"")) - 1, 0)


def load_configuration(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validate_files(
    output_dir: Path,
    expected_volumes: dict[str, int],
    manifest: dict[str, Any],
    report: ValidationReport,
) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for table_name, expected_rows in expected_volumes.items():
        csv_path = output_dir / "csv" / f"{table_name}.csv"
        parquet_path = output_dir / "parquet" / f"{table_name}.parquet"
        report.check(csv_path.exists(), f"Existe CSV de {table_name}", f"No existe {csv_path}")
        report.check(parquet_path.exists(), f"Existe Parquet de {table_name}", f"No existe {parquet_path}")
        if not csv_path.exists() or not parquet_path.exists():
            continue

        csv_rows = count_csv_rows(csv_path)
        parquet_rows = pq.ParquetFile(parquet_path).metadata.num_rows
        report.check(
            csv_rows == expected_rows,
            f"{table_name}: CSV contiene {expected_rows:,} filas",
            f"{table_name}: CSV contiene {csv_rows:,}; se esperaban {expected_rows:,}",
        )
        report.check(
            parquet_rows == expected_rows,
            f"{table_name}: Parquet contiene {expected_rows:,} filas",
            f"{table_name}: Parquet contiene {parquet_rows:,}; se esperaban {expected_rows:,}",
        )

        table_manifest = manifest.get(table_name, {})
        for output_format, path in (("csv", csv_path), ("parquet", parquet_path)):
            expected_hash = table_manifest.get("files", {}).get(output_format, {}).get("sha256")
            report.check(
                expected_hash is not None and sha256(path) == expected_hash,
                f"Hash SHA-256 válido para {table_name}.{output_format}",
                f"Hash inválido o ausente para {table_name}.{output_format}",
            )

        frame = pd.read_parquet(parquet_path)
        tables[table_name] = frame
        report.check(
            list(frame.columns) == EXPECTED_COLUMNS[table_name],
            f"{table_name}: estructura de columnas exacta",
            f"{table_name}: las columnas no coinciden con la especificación",
        )
    return tables


def validate_primary_keys(tables: dict[str, pd.DataFrame], report: ValidationReport) -> None:
    for table_name, primary_key in PRIMARY_KEYS.items():
        if table_name not in tables:
            continue
        frame = tables[table_name]
        valid = frame[primary_key].notna().all() and not frame[primary_key].duplicated().any()
        report.check(
            valid,
            f"{table_name}: llave primaria {primary_key} íntegra",
            f"{table_name}: {primary_key} contiene nulos o duplicados",
        )


def validate_referential_integrity(tables: dict[str, pd.DataFrame], report: ValidationReport) -> None:
    required = set(EXPECTED_COLUMNS)
    if not required.issubset(tables):
        report.check(False, "", "No se puede validar integridad referencial porque faltan tablas")
        return

    valid_clients = set(tables["TB_CLIENTES_CORE"]["id_cli"])
    valid_products = set(tables["TB_PRODUCTOS_CAT"]["cod_prod"])
    for table_name in ("TB_MOV_FINANCIEROS", "TB_OBLIGACIONES", "TB_COMISIONES_LOG"):
        frame = tables[table_name]
        invalid_clients = (~frame["id_cli"].isin(valid_clients)).sum()
        invalid_products = (~frame["cod_prod"].isin(valid_products)).sum()
        report.check(
            invalid_clients == 0,
            f"{table_name}: todos los clientes existen en TB_CLIENTES_CORE",
            f"{table_name}: hay {invalid_clients} referencias de cliente inválidas",
        )
        report.check(
            invalid_products == 0,
            f"{table_name}: todos los productos existen en TB_PRODUCTOS_CAT",
            f"{table_name}: hay {invalid_products} referencias de producto inválidas",
        )


def validate_nulls(
    tables: dict[str, pd.DataFrame],
    expected_percentage: float,
    smoke_test: bool,
    report: ValidationReport,
) -> None:
    tolerance = 0.025 if smoke_test else 0.01
    for table_name, columns in NULLABLE_COLUMNS.items():
        if table_name not in tables:
            continue
        frame = tables[table_name]
        for column in columns:
            actual = float(frame[column].isna().mean())
            report.check(
                abs(actual - expected_percentage) <= tolerance,
                f"{table_name}.{column}: nulos {actual:.2%} dentro de tolerancia",
                f"{table_name}.{column}: nulos {actual:.2%}; esperado aproximadamente {expected_percentage:.2%}",
            )


def validate_anomalies(
    movements: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    intended: dict[str, int],
    report: ValidationReport,
) -> dict[str, int]:
    movement_dates = pd.to_datetime(movements["fec_mov"])
    detected = {
        "duplicate_transactions": int(movements.duplicated(keep="first").sum()),
        "out_of_range_dates": int(((movement_dates < start_date) | (movement_dates > end_date)).sum()),
        "inconsistent_transaction_fields": int((movements["cod_canal"] == "CANAL_INVALIDO").sum()),
    }
    labels = {
        "duplicate_transactions": "movimientos duplicados",
        "out_of_range_dates": "fechas fuera de rango",
        "inconsistent_transaction_fields": "campos transaccionales inconsistentes",
    }
    for anomaly_name, intended_count in intended.items():
        detected_count = detected[anomaly_name]
        report.check(
            detected_count >= intended_count > 0,
            f"Anomalía detectada: {labels[anomaly_name]} ({detected_count})",
            f"No se detectó la cantidad esperada de {labels[anomaly_name]}: {detected_count}/{intended_count}",
        )
    return detected


def validate_business_consistency(tables: dict[str, pd.DataFrame], report: ValidationReport) -> None:
    obligations = tables.get("TB_OBLIGACIONES")
    if obligations is not None:
        valid_amounts = (
            (obligations["vr_aprobado"] >= obligations["vr_desembolsado"])
            & (obligations["vr_desembolsado"] >= obligations["sdo_capital"])
            & (obligations["sdo_capital"] >= 0)
        ).all()
        valid_dates = (
            pd.to_datetime(obligations["fec_venc"])
            >= pd.to_datetime(obligations["fec_desembolso"])
        ).all()
        report.check(valid_amounts, "Obligaciones: montos financieros consistentes", "Obligaciones: hay montos inconsistentes")
        report.check(valid_dates, "Obligaciones: vencimiento posterior al desembolso", "Obligaciones: hay fechas inconsistentes")

    products = tables.get("TB_PRODUCTOS_CAT")
    if products is not None:
        allowed = {"CREDITO_CONSUMO", "CREDITO_ROTATIVO", "TARJETA_DIGITAL", "CUENTA_AHORROS"}
        valid_types = set(products["tip_prod"]).issubset(allowed)
        report.check(valid_types, "Productos: tipos pertenecen al catálogo permitido", "Productos: hay tipos no permitidos")


def main() -> None:
    args = parse_arguments()
    config_path = args.config.resolve()
    config = load_configuration(config_path)
    output_dir = config_path.parents[1] / config["output"]["directory"]
    if args.smoke_test:
        output_dir = output_dir / "smoke"

    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] No existe el manifiesto: {manifest_path}")
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    expected_mode = "smoke-test" if args.smoke_test else "full"
    expected_volumes = SMOKE_VOLUMES if args.smoke_test else {
        name: int(volume) for name, volume in config["tables"].items()
    }
    report = ValidationReport()
    report.check(
        manifest.get("metadata", {}).get("mode") == expected_mode,
        f"Manifiesto corresponde al modo {expected_mode}",
        f"El manifiesto no corresponde al modo {expected_mode}",
    )

    tables = validate_files(output_dir, expected_volumes, manifest, report)
    validate_primary_keys(tables, report)
    validate_referential_integrity(tables, report)
    validate_nulls(
        tables,
        float(config["generation"]["null_percentage"]),
        args.smoke_test,
        report,
    )

    detected_anomalies: dict[str, int] = {}
    if "TB_MOV_FINANCIEROS" in tables:
        detected_anomalies = validate_anomalies(
            tables["TB_MOV_FINANCIEROS"],
            pd.Timestamp(config["generation"]["start_date"]),
            pd.Timestamp(config["generation"]["end_date"]),
            manifest["metadata"]["intentional_anomalies"],
            report,
        )
    validate_business_consistency(tables, report)

    result = {
        "status": "PASSED" if report.is_valid else "FAILED",
        "mode": expected_mode,
        "passed_checks": len(report.passed),
        "failed_checks": len(report.failed),
        "detected_anomalies": detected_anomalies,
        "failures": report.failed,
    }
    report_path = output_dir / "validation-report.json"
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"RESULTADO: {result['status']}")
    print(f"CONTROLES EXITOSOS: {len(report.passed)}")
    print(f"CONTROLES FALLIDOS: {len(report.failed)}")
    print(f"REPORTE: {report_path}")
    print("=" * 72)
    sys.exit(0 if report.is_valid else 1)


if __name__ == "__main__":
    main()