from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from pandera.errors import SchemaErrors


def _schema() -> DataFrameSchema:
    return DataFrameSchema(
        {
            "customer_id": Column(int, Check.ge(1), nullable=False),
            "email": Column(
                str,
                Check.str_matches(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
                nullable=False,
            ),
            "country": Column(str, Check.isin(["AR", "ES", "UY", "CL"]), nullable=False),
            "age": Column(int, Check.between(16, 90), nullable=False),
            "created_at": Column(pa.DateTime, nullable=False),
            "segment": Column(
                str,
                Check.isin(["Retail", "Online", "Wholesale"]),
                nullable=False,
            ),
        },
        strict=False,
    )


def _read_input(path: Path, sheet: str | int) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    raise ValueError("Input must be a CSV or Excel file (.csv, .xlsx, .xlsm).")


def _valid_rows(df: pd.DataFrame, schema: DataFrameSchema) -> pd.DataFrame:
    valid_positions: list[int] = []
    for position in range(len(df)):
        try:
            schema.validate(df.iloc[[position]], lazy=True)
        except SchemaErrors:
            continue
        valid_positions.append(position)
    return df.iloc[valid_positions].copy()


def run_validation(path: str, sheet: str | int, out_dir: str) -> bool:
    """Validate a dataset, write the report and valid rows, and return pass/fail."""
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = _read_input(input_path, sheet)
    df.columns = [str(column).strip().lower() for column in df.columns]
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    schema = _schema()
    report_md = [
        "# Data Quality Validation Report",
        "",
        f"- Input: **{input_path}**",
        f"- Rows: **{len(df)}**",
        "",
    ]

    try:
        valid_df = schema.validate(df, lazy=True)
        passed = True
        report_md.extend(["## Result: PASS", ""])
    except SchemaErrors as error:
        passed = False
        report_md.extend(["## Result: FAIL", "", "### Failure cases (top 50)", ""])
        report_md.append(error.failure_cases.head(50).to_markdown(index=False))
        report_md.append("")
        valid_df = _valid_rows(df, schema)

    report_path = output_dir / "validation_report.md"
    report_path.write_text("\n".join(report_md), encoding="utf-8")

    cleaned_path = output_dir / "cleaned.xlsx"
    valid_df.to_excel(cleaned_path, index=False, engine="openpyxl")

    print("OK - Wrote:")
    print(f"- {report_path}")
    print(f"- {cleaned_path}")
    return passed
