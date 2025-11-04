#!/usr/bin/env python3
"""
Add build information to CTRF report files.

Usage:
    python add_build_info_to_ctrf.py <report_path> <python_version> <arch> <os>

Example:
    python add_build_info_to_ctrf.py report.json 3.10 x86_64 ubuntu-latest
"""

import json
import os
import sys
from pathlib import Path


def add_build_info(report_file_path, python_ver, architecture, operating_system):
    """Add build metadata to CTRF report's extra field."""
    report_file = Path(report_file_path)

    if not report_file.exists():
        print(f"Error: Report file not found: {report_file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(report_file, "r", encoding="utf8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {report_file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure results object exists (it should based on CTRF spec)
    if "results" not in data:
        print("Warning: 'results' not found in CTRF report", file=sys.stderr)
        data["results"] = {}

    # Add extra field with build info
    if "extra" not in data["results"]:
        data["results"]["extra"] = {}

    # Add build metadata
    data["results"]["extra"]["build"] = {
        "python": python_ver,
        "arch": architecture,
        "os": operating_system,
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    }

    # Set suite name for grouping in the report
    # The 'suite' property belongs to each individual test object
    suite_name = f"{python_ver} | {architecture} | {operating_system}"
    if "tests" in data.get("results", {}):
        for test in data["results"]["tests"]:
            test["suite"] = suite_name
    else:
        print(f"Warning: No 'tests' array found in {report_file.name}", file=sys.stderr)

    # Write back to file
    with open(report_file, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)

    print(
        f"✅ Added build info to {report_file.name}: Python {python_ver}, {architecture}, {operating_system}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Usage: python add_build_info_to_ctrf.py <report_path> <python_version> <arch> <os>"
        )
        print(
            "Example: python add_build_info_to_ctrf.py report.json 3.10 x86_64 ubuntu-latest"
        )
        sys.exit(1)

    report_path = sys.argv[1]
    python_version = sys.argv[2]
    arch = sys.argv[3]
    os_name = sys.argv[4]

    add_build_info(report_path, python_version, arch, os_name)
