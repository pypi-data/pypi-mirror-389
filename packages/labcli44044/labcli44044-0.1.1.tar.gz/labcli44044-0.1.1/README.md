labmanager
=========

A small CLI tool to list and show Python lab programs stored in the repository's `program/` folder.

Quick usage (run from the repository root):

List available program files:

```powershell
python -m labmanager.cli list
```

Show a program file:

```powershell
python -m labmanager.cli show Average_Temperature_by_City.py
```

Install locally for global usage (editable/development install):

```powershell
pip install -e .
```

After installing, the `labcli` console script becomes available:

```powershell
labcli list
labcli show README.md
```

Install directly from GitHub (useful for other machines):

```powershell
pip install git+https://github.com/Shakthi44044/labcli.git
```

Publishing to PyPI (optional):

- Build the package: `python -m build` (requires `build` package)
- Upload with Twine: `python -m twine upload dist/*` (requires `twine`)

Notes
- `show` reads files as UTF-8. Use `--dir` if you installed the package and want to point to a different `program/` folder on disk.
- The package uses a console script `labcli` (configured in `pyproject.toml`).
