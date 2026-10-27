from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dq_suite.cli import main
from dq_suite.validate import run_validation


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _valid_customer() -> dict[str, object]:
    return {
        "customer_id": 1,
        "email": "customer@example.com",
        "country": "AR",
        "age": 28,
        "created_at": "2025-01-15T10:30:00",
        "segment": "Retail",
    }


def test_valid_csv_writes_pass_report_and_cleaned_workbook(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    output = tmp_path / "outputs"
    _write_csv(source, [_valid_customer()])

    passed = run_validation(str(source), 0, str(output))

    assert passed is True
    assert "## Result: PASS" in (output / "validation_report.md").read_text()
    cleaned = pd.read_excel(output / "cleaned.xlsx")
    assert cleaned.to_dict(orient="records")[0]["email"] == "customer@example.com"


def test_invalid_rows_are_excluded_from_cleaned_workbook(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    output = tmp_path / "outputs"
    valid = _valid_customer()
    invalid_email = {**_valid_customer(), "customer_id": 2, "email": "not-an-email"}
    invalid_age = {**_valid_customer(), "customer_id": 3, "age": 12}
    _write_csv(source, [valid, invalid_email, invalid_age])

    passed = run_validation(str(source), 0, str(output))

    assert passed is False
    report = (output / "validation_report.md").read_text()
    assert "## Result: FAIL" in report
    cleaned = pd.read_excel(output / "cleaned.xlsx")
    assert cleaned["customer_id"].tolist() == [1]


def test_missing_required_column_does_not_mark_any_row_as_clean(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    output = tmp_path / "outputs"
    customer = _valid_customer()
    customer.pop("email")
    _write_csv(source, [customer])

    passed = run_validation(str(source), 0, str(output))

    assert passed is False
    assert pd.read_excel(output / "cleaned.xlsx").empty


def test_missing_input_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        run_validation(str(tmp_path / "missing.csv"), 0, str(tmp_path / "outputs"))


def test_cli_returns_nonzero_when_dataset_fails_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "customers.csv"
    _write_csv(source, [{**_valid_customer(), "age": 12}])
    output = tmp_path / "outputs"
    monkeypatch.setattr(
        "sys.argv",
        ["dq_suite", "run", "--input", str(source), "--out", str(output)],
    )

    assert main() == 1


def test_cli_returns_zero_when_dataset_passes_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "customers.csv"
    _write_csv(source, [_valid_customer()])
    output = tmp_path / "outputs"
    monkeypatch.setattr(
        "sys.argv",
        ["dq_suite", "run", "--input", str(source), "--out", str(output)],
    )

    assert main() == 0
