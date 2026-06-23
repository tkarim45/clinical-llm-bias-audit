"""`geobias` command-line entry point.

    geobias run --config configs/oncqa_bedrock.yaml --seed 42   # run the audit pipeline
    geobias serve [--port 8000]                                 # FastAPI /audit service
    geobias dashboard                                           # Streamlit results dashboard
    geobias version
"""
from __future__ import annotations

import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geobias", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run the audit pipeline from a config")
    p_run.add_argument("--config", required=True)
    p_run.add_argument("--seed", type=int, default=42)
    p_run.add_argument("--limit", type=int, default=0, help="limit cases (0 = all)")
    p_run.add_argument("--parallelism", type=int, default=4)

    p_serve = sub.add_parser("serve", help="run the FastAPI /audit service")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)

    sub.add_parser("dashboard", help="launch the Streamlit results dashboard")
    sub.add_parser("version", help="print version")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        from .run import main as run_main
        return run_main([
            "--config", args.config, "--seed", str(args.seed),
            "--limit", str(args.limit), "--parallelism", str(args.parallelism),
        ])

    if args.cmd == "serve":
        import uvicorn
        uvicorn.run("api.main:app", host=args.host, port=args.port)
        return 0

    if args.cmd == "dashboard":
        import subprocess
        return subprocess.call([sys.executable, "-m", "streamlit", "run", "app/dashboard.py"])

    if args.cmd == "version":
        print(f"geobias {__version__}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
