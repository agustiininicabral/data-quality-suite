from __future__ import annotations
import os
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check
from pandera.errors import SchemaErrors

def _schema() -> DataFrameSchema:
    return DataFrameSchema({
        "customer_id": Column(int, Check.ge(1), nullable=False),
        "email": Column(str, Check.str_matches(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"), nullable=False),
        "country": Column(str, Check.isin(["AR","ES","UY","CL"]), nullable=False),
        "age": Column(int, Check.between(16, 90), nullable=False),
        "created_at": Column(pa.DateTime, nullable=False),
        "segment": Column(str, Check.isin(["Retail","Online","Wholesale"]), nullable=False),
    }, strict=False)

def run_validation(path: str, sheet, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")

    # Normalize
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    schema = _schema()

    report_md = ["# Data Quality Validation Report", ""]
    report_md.append(f"- Input: **{path}**")
    report_md.append(f"- Rows: **{len(df)}**")
    report_md.append("")

    try:
        validated = schema.validate(df, lazy=True)
        report_md.append("## Result: PASS")
        report_md.append("")
        valid_df = validated
    except SchemaErrors as e:
        report_md.append("## Result: FAIL")
        report_md.append("")
        failure = e.failure_cases.copy()
        report_md.append("### Failure cases (top 50)")
        report_md.append(failure.head(50).to_markdown(index=False))
        report_md.append("")
        # Keep valid rows only (best-effort)
        valid_df = df.copy()
        if "index" in failure.columns:
            bad_idx = set(failure["index"].dropna().astype(int).tolist())
            valid_df = valid_df[~valid_df.index.isin(bad_idx)]

    md_path = os.path.join(out_dir, "validation_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))

    cleaned_path = os.path.join(out_dir, "cleaned.xlsx")
    valid_df.to_excel(cleaned_path, index=False, engine="openpyxl")

    print("OK - Wrote:")
    print("-", md_path)
    print("-", cleaned_path)
