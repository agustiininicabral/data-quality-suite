# Data Quality Suite

CLI de validación de datos con Pandera, pandas y Excel/CSV. El proyecto valida un conjunto de reglas de negocio, genera un reporte Markdown y exporta a Excel únicamente las filas que pasan todas las reglas.

## Requisitos

- Python 3.12
- Dependencias de ejecución: `requirements.txt`
- Herramientas de desarrollo y pruebas: `requirements-dev.txt`

## Instalación (Windows PowerShell)

Desde la raíz del repositorio:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Ejecutar la demo

```powershell
.\.venv\Scripts\python.exe -m dq_suite run --input examples/customers.xlsx --sheet Customers --out outputs
```

El comando genera:

- `outputs/validation_report.md`: resultado PASS/FAIL, recuento de filas válidas/rechazadas y hasta 50 casos de error.
- `outputs/cleaned.xlsx`: filas que cumplen el esquema. Si falta una columna requerida, ninguna fila se considera válida.

Los nombres de columnas se normalizan a minúsculas y se eliminan espacios exteriores. Si esa normalización genera nombres duplicados (por ejemplo, `Email` y ` email `), el proceso detiene la ejecución con un error claro para evitar validar columnas ambiguas.

El proceso devuelve código de salida `0` si todas las filas cumplen el esquema y `1` si hay errores de validación. El archivo de ejemplo contiene errores intencionales para demostrar el reporte FAIL y el filtrado de filas; por eso, la ejecución de demo termina con código `1` de forma esperada. Los errores de entrada (archivo inexistente o extensión no compatible) se muestran como excepciones en lugar de confundirse con un resultado PASS/FAIL.

## Reglas de calidad

- `customer_id`: entero mayor o igual a 1.
- `email`: formato de correo básico, sin espacios.
- `country`: uno de `AR`, `ES`, `UY` o `CL`.
- `age`: entero entre 16 y 90.
- `created_at`: fecha/hora válida.
- `segment`: `Retail`, `Online` o `Wholesale`.

Los nombres de columnas se normalizan a minúsculas y se eliminan espacios exteriores. La validación no modifica el archivo de entrada. El archivo limpio se genera como un resultado separado; revisá siempre el reporte antes de usarlo en procesos posteriores.

## Pruebas y calidad

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff format --check dq_suite tests
.\.venv\Scripts\python.exe -m ruff check dq_suite tests
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub Actions ejecuta los mismos controles, corre la demo con el dataset incluido y publica los reportes como artefactos temporales. El workflow no necesita servicios externos.

## Estructura

- `dq_suite/validate.py`: esquema, validación, reporte y exportación de filas válidas.
- `dq_suite/cli.py` y `dq_suite/__main__.py`: interfaz de línea de comandos.
- `tests/`: pruebas de validación, filtrado de filas y códigos de salida.
- `examples/customers.xlsx`: dataset de demostración.

## Limitaciones

El esquema de ejemplo es deliberadamente pequeño. La validación de email es sintáctica y no confirma que una dirección exista. Las filas válidas solo se evalúan respecto de las reglas definidas; no se deduplican clientes ni se verifican datos contra fuentes externas.

## Licencia

MIT. Consultá [LICENSE](LICENSE).
