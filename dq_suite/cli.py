import argparse

from .validate import run_validation


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dq_suite",
        description="Pandera-based Data Quality Suite",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    run_parser = subparsers.add_parser("run", help="Run validation")
    run_parser.add_argument("--input", required=True, help="Path to Excel/CSV")
    run_parser.add_argument("--sheet", default=0, help="Excel sheet name/index")
    run_parser.add_argument("--out", default="outputs", help="Output folder")

    args = parser.parse_args()
    if args.cmd == "run":
        passed = run_validation(args.input, args.sheet, args.out)
        return 0 if passed else 1
    return 2
