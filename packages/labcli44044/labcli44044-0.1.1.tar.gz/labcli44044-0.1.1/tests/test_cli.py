import os
from pathlib import Path

from labmanager import cli


def test_list_contains_known_file():
    programs = cli.list_programs()
    # We expect README.md to be present in the program folder
    assert any(name.lower().startswith("readme") for name in programs)


def test_show_reads_file():
    programs_dir = cli.get_programs_dir()
    # pick a file that exists
    candidates = [p for p in programs_dir.iterdir() if p.is_file()]
    if not candidates:
        return
    name = candidates[0].name
    content = cli.show_program(name)
    assert isinstance(content, str)
    assert len(content) > 0
