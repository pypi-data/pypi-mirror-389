"""Command-line interface for listing and showing programs in the repo's `program/` folder."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List


def get_programs_dir() -> Path:
    """Return the path to the repository's `program/` directory.

    This is calculated relative to this file's location so the CLI works when
    run from the checkout (not necessarily when installed as a package).
    """
    # Prefer a `program/` folder in the current working directory so users can
    # run `labcli` from a project checkout without installing or republishing
    # the package.
    cwd_candidate = Path.cwd() / "program"
    if cwd_candidate.exists() and cwd_candidate.is_dir():
        return cwd_candidate

    # If the package was installed, the example programs live inside the
    # package at `labmanager/program`. Check for that first.
    package_dir = Path(__file__).resolve().parent
    package_programs = package_dir / "program"
    if package_programs.exists() and package_programs.is_dir():
        return package_programs

    # As a last-resort fallback (development checkout layout), look for a
    # top-level `program/` directory next to the package directory.
    repo_root = package_dir.parent
    repo_programs = repo_root / "program"
    return repo_programs


def list_programs(programs_dir: Path | None = None) -> List[str]:
    """Return a sorted list of files in `programs_dir`.

    Filters out directories and hidden files. Returns readable file names.
    """
    if programs_dir is None:
        programs_dir = get_programs_dir()
    if not programs_dir.exists() or not programs_dir.is_dir():
        return []
    result = [p.name for p in programs_dir.iterdir() if p.is_file() and not p.name.startswith('.')]
    return sorted(result, key=lambda s: s.lower())


def show_program(filename: str, programs_dir: Path | None = None) -> str:
    """Return the content of a file inside `programs_dir`.

    This function prevents directory traversal by only allowing names that
    resolve to files directly inside the `programs_dir`.
    """
    if programs_dir is None:
        programs_dir = get_programs_dir()
    candidate = Path(programs_dir) / filename
    try:
        candidate_resolved = candidate.resolve()
    except Exception:
        raise FileNotFoundError("Invalid file path")

    # Ensure the resolved path is directly inside the programs_dir
    if programs_dir.resolve() not in candidate_resolved.parents and candidate_resolved != programs_dir.resolve():
        raise FileNotFoundError("Requested file is outside the programs directory")

    if not candidate_resolved.exists() or not candidate_resolved.is_file():
        raise FileNotFoundError(f"File not found: {filename}")

    # Read as text and return
    return candidate_resolved.read_text(encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="labcli", description="List and show programs in the repository's program/ folder")
    sub = parser.add_subparsers(dest="command")

    sub_list = sub.add_parser("list", help="List available program files")
    sub_list.add_argument("--dir", help="Optional path to the programs directory", default=None)

    sub_show = sub.add_parser("show", help="Show the content of a program file")
    sub_show.add_argument("filename", help="File name to show (must exist in program/)")
    sub_show.add_argument("--dir", help="Optional path to the programs directory", default=None)

    args = parser.parse_args(argv)

    if args.command == "list":
        dirpath = Path(args.dir) if args.dir else None
        for name in list_programs(dirpath):
            print(name)
        return 0

    if args.command == "show":
        dirpath = Path(args.dir) if args.dir else None
        try:
            content = show_program(args.filename, dirpath)
            print(content)
            return 0
        except FileNotFoundError as e:
            print(str(e))
            return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
