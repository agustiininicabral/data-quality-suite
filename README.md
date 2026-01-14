# data-quality-suite

Suite de Data Quality con **pandera** (data contracts) para portfolio.
- Define un schema esperado
- Valida un dataset desde Excel/CSV
- Genera reporte PASS/FAIL con detalles
- Fácil de extender con nuevas reglas

## Run demo
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python -m dq_suite run --input examples/customers.xlsx --sheet Customers
```

Outputs:
- `outputs/validation_report.md`
- `outputs/cleaned.xlsx` (filas válidas)
