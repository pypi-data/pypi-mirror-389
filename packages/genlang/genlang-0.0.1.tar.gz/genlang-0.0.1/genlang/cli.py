#!/usr/bin/env python3
import sys
from pathlib import Path
from .core import run_genlang  # relative import

def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) == 3 and argv[1] == "run":
        path = Path(argv[2])
    elif len(argv) == 2:
        path = Path(argv[1])
    else:
        print("Usage: genlang run filepath.gen   OR   genlang filepath.gen", file=sys.stderr)
        return 2
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    source = path.read_text(encoding="utf-8")
    try:
        run_genlang(source, real_input=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
