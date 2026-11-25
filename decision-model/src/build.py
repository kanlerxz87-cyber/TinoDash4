#!/usr/bin/env python3
"""Build the site into decision-model/ and verify it before anything is committed.

    python3 build.py            # build + check + privacy scan
    python3 build.py --round 1000

This exists so the deployable output is always the checked output. Publishing an
unchecked build to a public GitHub Pages site is the one mistake in this project
that cannot be taken back, so the check is not optional here.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../site")
    ap.add_argument("--round", type=int, default=10)
    a = ap.parse_args()

    print(f"== build -> {a.out} (rounding step ${a.round})")
    rc = subprocess.call([sys.executable, "sitegen.py", "--out", a.out,
                          "--round", str(a.round)], cwd=ROOT)
    if rc:
        return rc

    print("== check")
    rc = subprocess.call([sys.executable, "tools/check_site.py", a.out], cwd=ROOT)
    if rc:
        print("\nBUILD REJECTED: the checker found errors. Nothing was published.")
        return rc

    print("\nOK — safe to commit and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
