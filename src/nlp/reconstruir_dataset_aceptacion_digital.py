#!/usr/bin/env python3
"""
Reconstruye de forma reproducible las podas y renombres manuales que llevaron
al dataset maestro de aceptacion digital usado en modelado.

Pipeline reproducido:
    datos_ml_0.xlsx
        -> datos_ml_3.xlsx
        -> datos_ml_4.xlsx
        -> datos_ml_5.xlsx
        -> datos_ml_master.xlsx
        -> datos_ml_master_1.xlsx
        -> datos_ml_master_2.xlsx
        -> datos_ml_master_3.xlsx
        -> datos_ml_master_4.xlsx
        -> datos_ml_master_indice_aceptacion_digital.xlsx

Por default escribe todo en un directorio separado para no sobreescribir los
artefactos historicos presentes en `data/processed/modeling/`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

try:
    from .generar_lags_datos_ml import build_readme, generate_lags, output_sheet_name, write_output
except ImportError:  # pragma: no cover - fallback para ejecucion directa
    from generar_lags_datos_ml import build_readme, generate_lags, output_sheet_name, write_output


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_ML0 = BASE_DIR / "data" / "processed" / "modeling" / "datos_ml_0.xlsx"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "processed" / "modeling" / "reconstruido_aceptacion_digital"

V5_NETO_COLUMNS = [
    "v5_agua_neto",
    "v5_alumbrado_neto",
    "v5_americo_neto",
    "v5_basura_neto",
    "v5_corrupcion_neto",
    "v5_delitos_neto",
    "v5_morena_neto",
    "v5_obras_neto",
    "v5_prevencion_neto",
    "v5_vialidad_neto",
]

V10_NETO_COLUMNS = [
    "v10_agua_neto",
    "v10_alumbrado_neto",
    "v10_americo_neto",
    "v10_basura_neto",
    "v10_corrupcion_neto",
    "v10_delitos_neto",
    "v10_morena_neto",
    "v10_obras_neto",
    "v10_prevencion_neto",
    "v10_vialidad_neto",
]

ML3_COLUMNS = [
    "fecha_inicio_semana",
    "semana_iso",
    "iso_year",
    "iso_week",
    "iso_yearweek_num",
    "target_serie_3e",
    "target_serie_4e",
    "has_full_pmi_features",
    "flag_missing_sentimiento_digital",
    "sentimiento_redes_ponderado",
    "sentimiento_medios",
    *V5_NETO_COLUMNS,
    *V10_NETO_COLUMNS,
]

ML5_COLUMNS = [
    "fecha_inicio_semana",
    "semana_iso",
    "iso_year",
    "iso_week",
    "iso_yearweek_num",
    "target_serie_4e",
    "has_full_pmi_features",
    "flag_missing_sentimiento_digital",
    "sentimiento_redes_ponderado",
    "sentimiento_medios",
    *V5_NETO_COLUMNS,
    "target_serie_4e_lag1",
    "target_serie_4e_lag2",
    "target_serie_4e_lag3",
    "target_serie_4e_lag4",
    "sentimiento_redes_ponderado_lag1",
    "sentimiento_redes_ponderado_lag2",
    "sentimiento_redes_ponderado_lag3",
    "sentimiento_redes_ponderado_lag4",
    "sentimiento_medios_lag1",
    "sentimiento_medios_lag2",
    "sentimiento_medios_lag3",
    "sentimiento_medios_lag4",
    *(f"{column}_lag{lag}" for column in V5_NETO_COLUMNS for lag in (1, 2, 3, 4)),
]

LEGACY_MASTER_COLUMNS = [
    "fecha_inicio_semana",
    "semana_iso",
    "iso_year",
    "iso_week",
    "iso_yearweek_num",
    "sentimiento_redes_ponderado",
    "sentimiento_medios",
    *V5_NETO_COLUMNS,
    "target_serie_4e_lag1",
    "target_serie_4e_lag2",
    "target_serie_4e_lag3",
    "target_serie_4e_lag4",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruye las podas manuales y el dataset maestro final de aceptacion digital.",
    )
    parser.add_argument(
        "--input-ml0",
        type=Path,
        default=DEFAULT_INPUT_ML0,
        help=f"Archivo base con sentimiento + PMI. Default: {DEFAULT_INPUT_ML0}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directorio donde se escribiran las salidas reconstruidas. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--sheet",
        default="ML_Ready_Train",
        help="Hoja de entrada dentro de datos_ml_0.xlsx. Default: ML_Ready_Train",
    )
    parser.add_argument(
        "--lags",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4],
        help="Lista de lags para reconstruir datos_ml_4. Default: 1 2 3 4",
    )
    return parser.parse_args()


def require_columns(df: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise SystemExit(f"Faltan columnas requeridas en {label}: {missing}")


def prune_columns(df: pd.DataFrame, keep_columns: list[str], label: str) -> pd.DataFrame:
    require_columns(df, keep_columns, label)
    return df[keep_columns].copy()


def apply_format(writer: pd.ExcelWriter, sheet_name: str, dataframe: pd.DataFrame) -> None:
    worksheet = writer.sheets[sheet_name]
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    fill = PatternFill("solid", fgColor="1F4E78")
    font = Font(color="FFFFFF", bold=True)
    for cell in worksheet[1]:
        cell.fill = fill
        cell.font = font

    for column_cells in worksheet.columns:
        letter = get_column_letter(column_cells[0].column)
        max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[letter].width = min(max(max_length + 2, 12), 36)


def write_single_sheet(
    path: Path,
    sheet_name: str,
    dataframe: pd.DataFrame,
    readme_rows: list[tuple[str, str]] | None = None,
    legacy_date_serial: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out_df = convert_legacy_date_column(dataframe) if legacy_date_serial else dataframe
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        out_df.to_excel(writer, sheet_name=sheet_name, index=False)
        apply_format(writer, sheet_name, out_df)
        if readme_rows:
            readme = pd.DataFrame(readme_rows, columns=["Campo", "Valor"])
            readme.to_excel(writer, sheet_name="README", index=False)
            apply_format(writer, "README", readme)


def excel_serial_to_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series)
    base = pd.Timestamp("1899-12-30")
    return base + pd.to_timedelta(pd.to_numeric(series), unit="D")


def datetime_to_excel_serial(series: pd.Series) -> pd.Series:
    if not pd.api.types.is_datetime64_any_dtype(series):
        return series
    base = pd.Timestamp("1899-12-30")
    return (pd.to_datetime(series) - base).dt.days


def convert_legacy_date_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "fecha_inicio_semana" in out.columns:
        out["fecha_inicio_semana"] = datetime_to_excel_serial(out["fecha_inicio_semana"])
    return out


def build_ml3(ml0_train: pd.DataFrame) -> pd.DataFrame:
    return prune_columns(ml0_train, ML3_COLUMNS, "datos_ml_0 -> datos_ml_3")


def build_ml4(ml3: pd.DataFrame, lag_values: list[int], output_path: Path) -> pd.DataFrame:
    lagged_df, summary = generate_lags(ml3, lag_values)
    # El artefacto historico `datos_ml_4.xlsx` no conserva los delta1 que hoy
    # produce el helper generico de lags.
    lagged_df = lagged_df.drop(
        columns=["target_serie_3e_delta1", "target_serie_4e_delta1"],
        errors="ignore",
    )
    summary["delta_columns_created"] = 0
    summary["original_columns"] = len(ml3.columns)
    summary["rows"] = len(lagged_df)
    readme = build_readme(
        input_path=Path("datos_ml_3.xlsx"),
        output_path=Path(output_path.name),
        lag_values=lag_values,
        summaries=[
            {
                **summary,
                "input_sheet": "ML_Ready_Train",
                "output_sheet": output_sheet_name("ML_Ready_Train"),
            }
        ],
    )
    write_output(output_path, {output_sheet_name("ML_Ready_Train"): convert_legacy_date_column(lagged_df)}, readme)
    return lagged_df


def build_ml5(ml4: pd.DataFrame) -> pd.DataFrame:
    return prune_columns(ml4, ML5_COLUMNS, "datos_ml_4 -> datos_ml_5")


def build_legacy_master(ml5: pd.DataFrame) -> pd.DataFrame:
    return prune_columns(ml5, LEGACY_MASTER_COLUMNS, "datos_ml_5 -> datos_ml_master")


def build_master_1(ml0_train: pd.DataFrame) -> pd.DataFrame:
    source_columns = [
        "fecha_inicio_semana",
        "semana_iso",
        "iso_year",
        "iso_week",
        "iso_yearweek_num",
        "target_serie_4e",
        "sentimiento_redes_ponderado",
        "sentimiento_medios",
        *V5_NETO_COLUMNS,
    ]
    base = prune_columns(ml0_train, source_columns, "datos_ml_0 -> datos_ml_master_1").rename(
        columns={"target_serie_4e": "serie_4e"},
    )
    for horizon in (1, 2, 3, 4):
        column_name = f"lead_tarjet_{horizon}w_serie_4e"
        base[column_name] = base["serie_4e"]
        base.loc[base.index < horizon, column_name] = pd.NA
    ordered_columns = [
        "fecha_inicio_semana",
        "semana_iso",
        "iso_year",
        "iso_week",
        "iso_yearweek_num",
        "serie_4e",
        "lead_tarjet_1w_serie_4e",
        "lead_tarjet_2w_serie_4e",
        "lead_tarjet_3w_serie_4e",
        "lead_tarjet_4w_serie_4e",
        "sentimiento_redes_ponderado",
        "sentimiento_medios",
        *V5_NETO_COLUMNS,
    ]
    return base[ordered_columns]


def build_master_2(master_1: pd.DataFrame) -> pd.DataFrame:
    out = master_1.drop(
        columns=[
            "lead_tarjet_1w_serie_4e",
            "lead_tarjet_2w_serie_4e",
            "lead_tarjet_3w_serie_4e",
            "lead_tarjet_4w_serie_4e",
        ]
    ).copy()
    for horizon in (1, 2, 3, 4):
        out[f"y_t+{horizon}"] = out["serie_4e"].shift(-horizon)
    ordered_columns = [
        "fecha_inicio_semana",
        "semana_iso",
        "iso_year",
        "iso_week",
        "iso_yearweek_num",
        "serie_4e",
        "y_t+1",
        "y_t+2",
        "y_t+3",
        "y_t+4",
        "sentimiento_redes_ponderado",
        "sentimiento_medios",
        *V5_NETO_COLUMNS,
    ]
    return out[ordered_columns]


def build_master_3(master_2: pd.DataFrame) -> pd.DataFrame:
    out = master_2[
        [
            "fecha_inicio_semana",
            "semana_iso",
            "serie_4e",
            "y_t+1",
            "y_t+2",
            "y_t+3",
            "y_t+4",
            "sentimiento_medios",
            *V5_NETO_COLUMNS,
        ]
    ].copy()
    return out.rename(
        columns={
            "serie_4e": "y_t",
            "y_t+1": "target_1w",
            "y_t+2": "target_2w",
            "y_t+3": "target_3w",
            "y_t+4": "target_4w",
        }
    )


def build_master_4(ml5: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "fecha_inicio_semana": ml5["fecha_inicio_semana"],
            "semana_iso": ml5["semana_iso"],
            "y_t": ml5["sentimiento_redes_ponderado"],
            "target_1w": ml5["sentimiento_redes_ponderado"].shift(-1),
            "target_2w": ml5["sentimiento_redes_ponderado"].shift(-2),
            "target_3w": ml5["sentimiento_redes_ponderado"].shift(-3),
            "target_4w": ml5["sentimiento_redes_ponderado"].shift(-4),
            "sentimiento_medios": ml5["sentimiento_medios"],
        }
    )
    for column in V5_NETO_COLUMNS:
        out[column] = ml5[column]
    return out


def build_master_indice(master_4: pd.DataFrame) -> pd.DataFrame:
    out = master_4.rename(
        columns={
            "y_t": "y_t_aceptacion_digital",
            "target_1w": "target_1w_aceptacion_digital",
            "target_2w": "target_2w_aceptacion_digital",
            "target_3w": "target_3w_aceptacion_digital",
            "target_4w": "target_4w_aceptacion_digital",
        }
    ).copy()
    out["fecha_inicio_semana"] = excel_serial_to_datetime(out["fecha_inicio_semana"])
    return out


def main() -> None:
    args = parse_args()
    input_ml0 = args.input_ml0.expanduser()
    output_dir = args.output_dir.expanduser()
    lag_values = sorted(set(args.lags))

    if not input_ml0.exists():
        raise SystemExit(f"No existe el archivo de entrada: {input_ml0}")

    print("=" * 72)
    print("RECONSTRUCCION DE DATASET DE ACEPTACION DIGITAL")
    print("=" * 72)
    print(f"Input ML_0:  {input_ml0}")
    print(f"Output dir:  {output_dir}")
    print(f"Lags ML_4:   {', '.join(str(lag) for lag in lag_values)}")

    ml0_train = pd.read_excel(input_ml0, sheet_name=args.sheet)

    ml3 = build_ml3(ml0_train)
    ml3_path = output_dir / "datos_ml_3.xlsx"
    write_single_sheet(
        ml3_path,
        "ML_Ready_Train",
        ml3,
        readme_rows=[
            ("Paso", "Poda manual reproducida desde datos_ml_0.xlsx"),
            ("Archivo fuente", input_ml0.name),
            ("Columnas salida", str(len(ml3.columns))),
        ],
        legacy_date_serial=True,
    )
    print(f"- datos_ml_3.xlsx: {len(ml3.columns)} columnas")

    ml4_path = output_dir / "datos_ml_4.xlsx"
    ml4 = build_ml4(ml3, lag_values, ml4_path)
    print(f"- datos_ml_4.xlsx: {len(ml4.columns)} columnas")

    ml5 = build_ml5(ml4)
    ml5_path = output_dir / "datos_ml_5.xlsx"
    write_single_sheet(
        ml5_path,
        "ML_Lagged_Train",
        ml5,
        readme_rows=[
            ("Paso", "Poda manual reproducida desde datos_ml_4.xlsx"),
            ("Archivo fuente", ml4_path.name),
            ("Columnas salida", str(len(ml5.columns))),
        ],
        legacy_date_serial=True,
    )
    print(f"- datos_ml_5.xlsx: {len(ml5.columns)} columnas")

    legacy_master = build_legacy_master(ml5)
    legacy_master_path = output_dir / "datos_ml_master.xlsx"
    write_single_sheet(
        legacy_master_path,
        "ML_Lagged_Train",
        legacy_master,
        readme_rows=[
            ("Paso", "Poda manual reproducida desde datos_ml_5.xlsx"),
            ("Archivo fuente", ml5_path.name),
            ("Columnas salida", str(len(legacy_master.columns))),
        ],
        legacy_date_serial=True,
    )
    print(f"- datos_ml_master.xlsx: {len(legacy_master.columns)} columnas")

    master_1 = build_master_1(ml0_train)
    write_single_sheet(output_dir / "datos_ml_master_1.xlsx", "Sheet1", master_1, legacy_date_serial=True)

    master_2 = build_master_2(master_1)
    write_single_sheet(output_dir / "datos_ml_master_2.xlsx", "Sheet1", master_2, legacy_date_serial=True)

    master_3 = build_master_3(master_2)
    write_single_sheet(output_dir / "datos_ml_master_3.xlsx", "Sheet1", master_3, legacy_date_serial=True)

    master_4 = build_master_4(ml5)
    write_single_sheet(output_dir / "datos_ml_master_4.xlsx", "Sheet1", master_4, legacy_date_serial=True)

    master_indice = build_master_indice(master_4)
    write_single_sheet(
        output_dir / "datos_ml_master_indice_aceptacion_digital.xlsx",
        "Sheet1",
        master_indice,
    )
    print(f"- datos_ml_master_indice_aceptacion_digital.xlsx: {len(master_indice.columns)} columnas")
    print("=" * 72)


if __name__ == "__main__":
    main()
