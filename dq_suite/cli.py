import argparse
from .validate import run_validation

def main():
    p = argparse.ArgumentParser(prog="dq_suite", description="Pandera-based Data Quality Suite")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run validation")
    run.add_argument("--input", required=True, help="Path to Excel/CSV")
    run.add_argument("--sheet", default=0, help="Excel sheet name/index")
    run.add_argument("--out", default="outputs", help="Output folder")

    args = p.parse_args()
    if args.cmd == "run":
        run_validation(args.input, args.sheet, args.out)
