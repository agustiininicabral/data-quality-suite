from pathlib import Path

import pandas as pd
import pytest

from dq_suite.validate import run_validation


def _customer(customer_id: int = 1, age: int = 28) -> dict[str, object]:
    return {
        "customer_id": customer_id,
        "email": f"customer{customer_id}@example.com",
        "country": "AR",
        "age": age,
        "created_at": "2025-01-15T10:30:00",
        "segment": "Retail",
    }


def test_report_counts_valid_and_rejected_rows(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    output = tmp_path / "out"
    pd.DataFrame([_customer(1), _customer(2, age=12)]).to_csv(source, index=False)

    assert run_validation(str(source), 0, str(output)) is False

    report = (output / "validation_report.md").read_text(encoding="utf-8")
    assert "- Rows received: **2**" in report
    assert "- Valid rows: **1**" in report
    assert "- Rejected rows: **1**" in report


def test_duplicate_headers_after_normalization_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "duplicate_headers.csv"
    pd.DataFrame(
        [{"customer_id": 1, "Email": "one@example.com", " email ": "two@example.com"}]
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="Duplicate column names after normalization: email"):
        run_validation(str(source), 0, str(tmp_path / "out"))


def test_empty_dataset_fails_validation(tmp_path: Path) -> None:
    source = tmp_path / "empty.csv"
    source.write_text(
        "customer_id,email,country,age,created_at,segment\\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"

    assert run_validation(str(source), 0, str(output)) is False
    report = (output / "validation_report.md").read_text(encoding="utf-8")
    assert "## Result: FAIL" in report
    assert "Input contains no data rows" in report
    assert pd.read_excel(output / "cleaned.xlsx").empty
