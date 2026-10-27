from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors
from pandera.pandas import Check, Column, DataFrameSchema


def _schema() -> DataFrameSchema:
    return DataFrameSchema(
        {
            "customer_id": Column(int, Check.ge(1), nullable=False),
            "email": Column(
                str,
                Check.str_matches(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
                nullable=False,
            ),
            "country": Column(
                str, Check.isin(["AR", "ES", "UY", "CL"]), nullable=False
            ),
            "age": Column(int, Check.between(16, 90), nullable=False),
            "created_at": Column(pa.DateTime, nullable=False),
            "segment": Column(
                str, Check.isin(["Retail", "Online", "Wholesale"]), nullable=False
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
    valid_rows: list[pd.DataFrame] = []
    integer_columns = ("customer_id", "age")
    for position in range(len(df)):
        candidate = df.iloc[[position]].copy()
        for column in integer_columns:
            if column not in candidate.columns:
                continue
            value = candidate.iloc[0][column]
            if pd.isna(value):
                continue
            numeric = pd.to_numeric(value, errors="coerce")
            if pd.notna(numeric) and float(numeric).is_integer():
                candidate[column] = pd.Series(
                    [int(numeric)], index=candidate.index, dtype="int64"
                )
        try:
            schema.validate(candidate, lazy=True)
        except SchemaErrors:
            continue
        valid_rows.append(candidate)
    if not valid_rows:
        return df.iloc[0:0].copy()
    return pd.concat(valid_rows, axis=0).copy()


def run_validation(path: str, sheet: str | int, out_dir: str) -> bool:
    """Validate input, write a report and valid rows, and return pass/fail."""
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = _read_input(input_path, sheet)
    df.columns = [str(column).strip().lower() for column in df.columns]
    duplicates = sorted(
        {column for column in df.columns if list(df.columns).count(column) > 1}
    )
    if duplicates:
        raise ValueError(
            "Duplicate column names after normalization: " + ", ".join(duplicates)
        )
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    if df.empty:
        report_path = output_dir / "validation_report.md"
        report_path.write_text(
            "\n".join(
                [
                    "# Data Quality Validation Report",
                    "",
                    f"- Input: **{input_path}**",
                    "- Rows received: **0**",
                    "",
                    "## Result: FAIL",
                    "",
                    "- Valid rows: **0**",
                    "- Rejected rows: **0**",
                    "- Reason: Input contains no data rows.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        cleaned_path = output_dir / "cleaned.xlsx"
        df.to_excel(cleaned_path, index=False, engine="openpyxl")
        print("FAIL - Input contains no data rows.")
        print(f"- {report_path}")
        print(f"- {cleaned_path}")
        return False

    schema = _schema()
    report_md = [
        "# Data Quality Validation Report",
        "",
        f"- Input: **{input_path}**",
        f"- Rows received: **{len(df)}**",
        "",
    ]

    try:
        valid_df = schema.validate(df, lazy=True)
        passed = True
        report_md.extend(
            [
                "## Result: PASS",
                "",
                f"- Valid rows: **{len(valid_df)}**",
                "- Rejected rows: **0**",
                "",
            ]
        )
    except SchemaErrors as error:
        passed = False
        valid_df = _valid_rows(df, schema)
        rejected_count = len(df) - len(valid_df)
        report_md.extend(
            [
                "## Result: FAIL",
                "",
                f"- Valid rows: **{len(valid_df)}**",
                f"- Rejected rows: **{rejected_count}**",
                "",
                "### Failure cases (top 50)",
                "",
                error.failure_cases.head(50).to_markdown(index=False),
                "",
            ]
        )

    report_path = output_dir / "validation_report.md"
    report_path.write_text("\n".join(report_md), encoding="utf-8")
    cleaned_path = output_dir / "cleaned.xlsx"
    valid_df.to_excel(cleaned_path, index=False, engine="openpyxl")

    print("OK - Wrote:")
    print(f"- {report_path}")
    print(f"- {cleaned_path}")
    return passed
