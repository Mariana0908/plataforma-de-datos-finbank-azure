"""Generador reproducible de datos sintéticos para FinBank."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from faker import Faker


LOGGER = logging.getLogger("finbank-generator")
SCRIPT_PATH = Path(__file__).resolve()


LOCATIONS = [
    ("COBOG", "Colombia", "Bogotá", "Cundinamarca", 4.7110, -74.0721),
    ("COMDE", "Colombia", "Medellín", "Antioquia", 6.2442, -75.5812),
    ("COCAL", "Colombia", "Cali", "Valle del Cauca", 3.4516, -76.5320),
    ("COBAQ", "Colombia", "Barranquilla", "Atlántico", 10.9685, -74.7813),
    ("MXCMX", "Mexico", "Ciudad de México", "Ciudad de México", 19.4326, -99.1332),
    ("MXGDL", "Mexico", "Guadalajara", "Jalisco", 20.6597, -103.3496),
    ("MXMTY", "Mexico", "Monterrey", "Nuevo León", 25.6866, -100.3161),
    ("MXPUE", "Mexico", "Puebla", "Puebla", 19.0414, -98.2063),
    ("PELIM", "Peru", "Lima", "Lima", -12.0464, -77.0428),
    ("PEAQP", "Peru", "Arequipa", "Arequipa", -16.4090, -71.5375),
    ("PECUS", "Peru", "Cusco", "Cusco", -13.5319, -71.9675),
    ("PETRU", "Peru", "Trujillo", "La Libertad", -8.1116, -79.0288),
    ("CLSCL", "Chile", "Santiago", "Región Metropolitana", -33.4489, -70.6693),
    ("CLVAP", "Chile", "Valparaíso", "Valparaíso", -33.0472, -71.6127),
    ("CLCCP", "Chile", "Concepción", "Biobío", -36.8201, -73.0444),
    ("CLANT", "Chile", "Antofagasta", "Antofagasta", -23.6509, -70.3975),
    ("ARBUE", "Argentina", "Buenos Aires", "Buenos Aires", -34.6037, -58.3816),
    ("ARCOR", "Argentina", "Córdoba", "Córdoba", -31.4201, -64.1888),
    ("ARROS", "Argentina", "Rosario", "Santa Fe", -32.9442, -60.6505),
    ("ARMEN", "Argentina", "Mendoza", "Mendoza", -32.8895, -68.8458),
]


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
        help="Ejecuta una prueba rápida con volúmenes reducidos en output/smoke.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    required_tables = {
        "TB_CLIENTES_CORE",
        "TB_PRODUCTOS_CAT",
        "TB_MOV_FINANCIEROS",
        "TB_OBLIGACIONES",
        "TB_SUCURSALES_RED",
        "TB_COMISIONES_LOG",
    }
    missing = required_tables.difference(config.get("tables", {}))
    if missing:
        raise ValueError(f"Faltan tablas en la configuración: {sorted(missing)}")

    start_date = pd.Timestamp(config["generation"]["start_date"])
    end_date = pd.Timestamp(config["generation"]["end_date"])
    if end_date <= start_date or (end_date - start_date).days < 365:
        raise ValueError("El rango de generación debe cubrir al menos 365 días.")

    return config


def random_dates(
    rng: np.random.Generator,
    start: pd.Timestamp,
    end: pd.Timestamp,
    size: int,
) -> pd.DatetimeIndex:
    day_offsets = rng.integers(0, (end - start).days + 1, size=size)
    return pd.to_datetime(start + pd.to_timedelta(day_offsets, unit="D"))


def add_nulls(
    frame: pd.DataFrame,
    columns: list[str],
    percentage: float,
    rng: np.random.Generator,
) -> None:
    quantity = round(len(frame) * percentage)
    for column in columns:
        indexes = rng.choice(frame.index.to_numpy(), size=quantity, replace=False)
        frame.loc[indexes, column] = pd.NA


def generate_products(volume: int, rng: np.random.Generator) -> pd.DataFrame:
    product_types = np.resize(
        np.array(
            [
                "CREDITO_CONSUMO",
                "CREDITO_ROTATIVO",
                "TARJETA_DIGITAL",
                "CUENTA_AHORROS",
            ]
        ),
        volume,
    )
    rng.shuffle(product_types)
    descriptions = {
        "CREDITO_CONSUMO": "Crédito de consumo",
        "CREDITO_ROTATIVO": "Crédito rotativo",
        "TARJETA_DIGITAL": "Tarjeta digital",
        "CUENTA_AHORROS": "Cuenta de ahorros digital",
    }

    rows = []
    for index, product_type in enumerate(product_types, start=1):
        is_credit = product_type != "CUENTA_AHORROS"
        rows.append(
            {
                "cod_prod": f"PRD{index:03d}",
                "desc_prod": f"{descriptions[product_type]} {index:02d}",
                "tip_prod": product_type,
                "tasa_ea": round(float(rng.uniform(8, 30)), 2) if is_credit else round(float(rng.uniform(0.1, 8)), 2),
                "plazo_max_meses": int(rng.choice([6, 12, 18, 24, 36, 48, 60])) if is_credit else 0,
                "cuota_min": round(float(rng.uniform(20_000, 250_000)), 2) if is_credit else 0.0,
                "comision_admin": round(float(rng.uniform(0, 35_000)), 2),
                "estado_prod": rng.choice(["ACTIVO", "INACTIVO"], p=[0.92, 0.08]),
            }
        )
    return pd.DataFrame(rows)


def generate_branches(volume: int, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for index in range(1, volume + 1):
        _, _, city, department, latitude, longitude = LOCATIONS[(index - 1) % len(LOCATIONS)]
        point_type = rng.choice(["SUCURSAL", "CORRESPONSAL", "PUNTO_DIGITAL"], p=[0.35, 0.5, 0.15])
        rows.append(
            {
                "cod_suc": f"SUC{index:04d}",
                "nom_suc": f"{point_type.title().replace('_', ' ')} {city} {index:03d}",
                "tip_punto": point_type,
                "ciudad": city,
                "depto": department,
                "latitud": round(float(latitude + rng.normal(0, 0.025)), 6),
                "longitud": round(float(longitude + rng.normal(0, 0.025)), 6),
                "activo": rng.choice([True, False], p=[0.94, 0.06]),
            }
        )
    return pd.DataFrame(rows)


def generate_clients(
    volume: int,
    rng: np.random.Generator,
    fake: Faker,
    end_date: pd.Timestamp,
    null_percentage: float,
) -> pd.DataFrame:
    rows = []
    segments = ["BASICO", "ESTANDAR", "PREMIUM", "ELITE"]
    for index in range(1, volume + 1):
        _, country, city, department, _, _ = LOCATIONS[rng.integers(0, len(LOCATIONS))]
        document_type = {
            "Colombia": "CC",
            "Mexico": "CURP",
            "Peru": "DNI",
            "Chile": "RUT",
            "Argentina": "DNI",
        }[country]
        rows.append(
            {
                "id_cli": index,
                "nomb_cli": fake.first_name(),
                "apell_cli": fake.last_name(),
                "tip_doc": document_type,
                "num_doc": f"{index:010d}{rng.integers(10, 99)}",
                "fec_nac": random_dates(rng, pd.Timestamp("1945-01-01"), pd.Timestamp("2007-12-31"), 1)[0],
                "fec_alta": random_dates(rng, pd.Timestamp("2016-01-01"), end_date, 1)[0],
                "cod_segmento": rng.choice(segments, p=[0.46, 0.34, 0.16, 0.04]),
                "score_buro": int(np.clip(rng.normal(650, 95), 300, 850)),
                "ciudad_res": city,
                "depto_res": department,
                "estado_cli": rng.choice(["ACTIVO", "INACTIVO", "BLOQUEADO"], p=[0.91, 0.07, 0.02]),
                "canal_adquis": rng.choice(["APP", "WEB", "SUCURSAL", "REFERIDO"], p=[0.48, 0.24, 0.18, 0.10]),
            }
        )
    clients = pd.DataFrame(rows)
    add_nulls(clients, ["score_buro", "canal_adquis"], null_percentage, rng)
    return clients


def generate_obligations(
    volume: int,
    clients: pd.DataFrame,
    products: pd.DataFrame,
    rng: np.random.Generator,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    null_percentage: float,
) -> pd.DataFrame:
    credit_codes = products.loc[products["tip_prod"] != "CUENTA_AHORROS", "cod_prod"].to_numpy()
    client_ids = rng.choice(clients["id_cli"].to_numpy(), size=volume)
    product_codes = rng.choice(credit_codes, size=volume)
    approved = np.round(np.clip(rng.lognormal(15.2, 0.9, volume), 500_000, 120_000_000), 2)
    disbursed = np.round(approved * rng.uniform(0.75, 1.0, volume), 2)
    paid_fraction = rng.beta(2.2, 2.0, volume)
    principal = np.round(disbursed * (1 - paid_fraction), 2)
    terms = rng.choice([6, 12, 18, 24, 36, 48, 60], size=volume, p=[0.05, 0.24, 0.10, 0.26, 0.17, 0.10, 0.08])
    installments_pending = np.maximum(1, np.ceil(terms * (1 - paid_fraction))).astype(int)
    installments = np.maximum(1, terms)
    payment = np.round(disbursed / installments * rng.uniform(1.02, 1.18, volume), 2)
    disbursement_dates = random_dates(rng, start_date - pd.DateOffset(months=12), end_date, volume)
    due_dates = disbursement_dates + pd.to_timedelta(terms * 30, unit="D")
    days_past_due = rng.choice(
        np.concatenate([np.array([0]), np.arange(1, 181)]),
        size=volume,
        p=np.concatenate([np.array([0.70]), np.repeat(0.30 / 180, 180)]),
    )
    risk = pd.cut(
        days_past_due,
        bins=[-1, 0, 30, 60, 90, np.inf],
        labels=["A", "B", "C", "D", "E"],
    ).astype("string")

    obligations = pd.DataFrame(
        {
            "id_oblig": np.arange(1, volume + 1),
            "id_cli": client_ids,
            "cod_prod": product_codes,
            "vr_aprobado": approved,
            "vr_desembolsado": disbursed,
            "sdo_capital": principal,
            "vr_cuota": payment,
            "fec_desembolso": disbursement_dates,
            "fec_venc": due_dates,
            "dias_mora_act": days_past_due,
            "num_cuotas_pend": installments_pending,
            "calif_riesgo": risk,
        }
    )
    add_nulls(obligations, ["calif_riesgo"], null_percentage, rng)
    return obligations


def generate_movements(
    volume: int,
    clients: pd.DataFrame,
    products: pd.DataFrame,
    rng: np.random.Generator,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    null_percentage: float,
    anomaly_config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    duplicate_percentage = float(anomaly_config["duplicate_transactions"]["percentage"])
    duplicate_count = round(volume * duplicate_percentage) if anomaly_config["duplicate_transactions"]["enabled"] else 0
    unique_count = volume - duplicate_count

    client_ids = rng.choice(clients["id_cli"].to_numpy(), size=unique_count)
    product_codes = rng.choice(products["cod_prod"].to_numpy(), size=unique_count)
    dates = pd.Series(random_dates(rng, start_date, end_date, unique_count))
    seconds = rng.integers(0, 24 * 60 * 60, size=unique_count)
    hours = pd.to_datetime(seconds, unit="s").strftime("%H:%M:%S")
    transaction_types = rng.choice(
        ["COMPRA", "TRANSFERENCIA", "RETIRO", "DEPOSITO", "PAGO", "PSE", "ACH"],
        size=unique_count,
        p=[0.31, 0.22, 0.10, 0.10, 0.12, 0.09, 0.06],
    )
    channels = rng.choice(
        ["APP", "WEB", "ATM", "PSE", "ACH", "CORRESPONSAL", "SUCURSAL"],
        size=unique_count,
        p=[0.38, 0.16, 0.12, 0.08, 0.07, 0.12, 0.07],
    )
    city_codes = rng.choice(np.array([location[0] for location in LOCATIONS]), size=unique_count)
    amounts = np.round(np.clip(rng.lognormal(12.2, 1.15, unique_count), 1_000, 80_000_000), 2)

    movements = pd.DataFrame(
        {
            "id_mov": np.arange(1, unique_count + 1),
            "id_cli": client_ids,
            "cod_prod": product_codes,
            "num_cuenta": [f"CTA{client_id:08d}{product_code[-3:]}" for client_id, product_code in zip(client_ids, product_codes, strict=True)],
            "fec_mov": dates,
            "hra_mov": hours,
            "vr_mov": amounts,
            "tip_mov": transaction_types,
            "cod_canal": channels,
            "cod_ciudad": city_codes,
            "cod_estado_mov": rng.choice(["APROBADO", "RECHAZADO", "REVERSADO"], size=unique_count, p=[0.94, 0.04, 0.02]),
            "id_dispositivo": [f"DEV{value:09d}" for value in rng.integers(1, max(2, len(clients) * 2), size=unique_count)],
        }
    )
    add_nulls(movements, ["id_dispositivo"], null_percentage, rng)

    out_of_range_count = 0
    out_of_range_config = anomaly_config["out_of_range_dates"]
    if out_of_range_config["enabled"]:
        out_of_range_count = round(volume * float(out_of_range_config["percentage"]))
        indexes = rng.choice(movements.index, size=out_of_range_count, replace=False)
        movements.loc[indexes, "fec_mov"] = start_date - pd.to_timedelta(rng.integers(1, 91, out_of_range_count), unit="D")

    inconsistent_count = 0
    inconsistent_config = anomaly_config["inconsistent_transaction_fields"]
    if inconsistent_config["enabled"]:
        inconsistent_count = round(volume * float(inconsistent_config["percentage"]))
        indexes = rng.choice(movements.index, size=inconsistent_count, replace=False)
        movements.loc[indexes, "cod_canal"] = "CANAL_INVALIDO"

    if duplicate_count:
        duplicate_rows = movements.sample(n=duplicate_count, replace=False, random_state=int(rng.integers(0, 2**31 - 1)))
        movements = pd.concat([movements, duplicate_rows], ignore_index=True)

    movements = movements.sample(frac=1, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
    anomaly_counts = {
        "duplicate_transactions": duplicate_count,
        "out_of_range_dates": out_of_range_count,
        "inconsistent_transaction_fields": inconsistent_count,
    }
    return movements, anomaly_counts


def generate_commissions(
    volume: int,
    clients: pd.DataFrame,
    products: pd.DataFrame,
    rng: np.random.Generator,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    null_percentage: float,
) -> pd.DataFrame:
    commissions = pd.DataFrame(
        {
            "id_comision": np.arange(1, volume + 1),
            "id_cli": rng.choice(clients["id_cli"].to_numpy(), size=volume),
            "cod_prod": rng.choice(products["cod_prod"].to_numpy(), size=volume),
            "fec_cobro": random_dates(rng, start_date, end_date, volume),
            "vr_comision": np.round(np.clip(rng.lognormal(9.3, 0.8, volume), 500, 500_000), 2),
            "tip_comision": rng.choice(
                ["ADMINISTRACION", "RETIRO", "TRANSFERENCIA", "CUOTA_MANEJO", "SEGURO"],
                size=volume,
                p=[0.18, 0.18, 0.20, 0.28, 0.16],
            ),
            "estado_cobro": rng.choice(["COBRADA", "PENDIENTE", "REVERSADA"], size=volume, p=[0.88, 0.09, 0.03]),
        }
    )
    add_nulls(commissions, ["tip_comision"], null_percentage, rng)
    return commissions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_tables(
    tables: dict[str, pd.DataFrame],
    output_dir: Path,
    formats: list[str],
    separator: str,
    encoding: str,
) -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for table_name, frame in tables.items():
        manifest[table_name] = {"rows": len(frame), "columns": list(frame.columns), "files": {}}
        for output_format in formats:
            format_dir = output_dir / output_format
            format_dir.mkdir(parents=True, exist_ok=True)
            if output_format == "csv":
                path = format_dir / f"{table_name}.csv"
                frame.to_csv(path, index=False, sep=separator, encoding=encoding, date_format="%Y-%m-%d")
            elif output_format == "parquet":
                path = format_dir / f"{table_name}.parquet"
                frame.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
            else:
                raise ValueError(f"Formato no soportado: {output_format}")
            manifest[table_name]["files"][output_format] = {
                "path": str(path.relative_to(output_dir.parent)),
                "sha256": sha256(path),
            }
            LOGGER.info("%s: %s registros escritos en %s", table_name, len(frame), path)
    return manifest


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_arguments()
    config = load_config(args.config.resolve())
    generation = config["generation"]
    seed = int(generation["seed"])
    rng = np.random.default_rng(seed)
    Faker.seed(seed)
    fake = Faker("es_CO")
    fake.seed_instance(seed)

    start_date = pd.Timestamp(generation["start_date"])
    end_date = pd.Timestamp(generation["end_date"])
    null_percentage = float(generation["null_percentage"])
    volumes = dict(config["tables"])
    if args.smoke_test:
        volumes.update(
            {
                "TB_CLIENTES_CORE": 100,
                "TB_PRODUCTOS_CAT": 10,
                "TB_MOV_FINANCIEROS": 2_000,
                "TB_OBLIGACIONES": 300,
                "TB_SUCURSALES_RED": 20,
                "TB_COMISIONES_LOG": 500,
            }
        )
        LOGGER.info("Modo smoke test activo: se utilizarán volúmenes reducidos")

    LOGGER.info("Generando catálogo de productos")
    products = generate_products(int(volumes["TB_PRODUCTOS_CAT"]), rng)
    LOGGER.info("Generando red de sucursales")
    branches = generate_branches(int(volumes["TB_SUCURSALES_RED"]), rng)
    LOGGER.info("Generando clientes")
    clients = generate_clients(int(volumes["TB_CLIENTES_CORE"]), rng, fake, end_date, null_percentage)
    LOGGER.info("Generando obligaciones")
    obligations = generate_obligations(
        int(volumes["TB_OBLIGACIONES"]), clients, products, rng, start_date, end_date, null_percentage
    )
    LOGGER.info("Generando movimientos financieros")
    movements, anomaly_counts = generate_movements(
        int(volumes["TB_MOV_FINANCIEROS"]),
        clients,
        products,
        rng,
        start_date,
        end_date,
        null_percentage,
        config["anomalies"],
    )
    LOGGER.info("Generando comisiones")
    commissions = generate_commissions(
        int(volumes["TB_COMISIONES_LOG"]), clients, products, rng, start_date, end_date, null_percentage
    )

    tables = {
        "TB_CLIENTES_CORE": clients,
        "TB_PRODUCTOS_CAT": products,
        "TB_MOV_FINANCIEROS": movements,
        "TB_OBLIGACIONES": obligations,
        "TB_SUCURSALES_RED": branches,
        "TB_COMISIONES_LOG": commissions,
    }
    project_dir = args.config.resolve().parents[1]
    output_dir = project_dir / config["output"]["directory"]
    if args.smoke_test:
        output_dir = output_dir / "smoke"
    manifest = save_tables(
        tables,
        output_dir,
        list(config["output"]["formats"]),
        str(config["output"]["csv_separator"]),
        str(config["output"]["csv_encoding"]),
    )
    manifest["metadata"] = {
        "seed": seed,
        "start_date": str(start_date.date()),
        "end_date": str(end_date.date()),
        "null_percentage": null_percentage,
        "intentional_anomalies": anomaly_counts,
        "mode": "smoke-test" if args.smoke_test else "full",
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Generación completada. Manifiesto: %s", manifest_path)


if __name__ == "__main__":
    main()