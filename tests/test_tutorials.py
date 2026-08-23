# tests/test_tutorials.py
"""Tutorials cannot rot: every code cell of every notebook in tutorials/
is executed top-to-bottom. Any exception fails the suite."""
import json
import pathlib

import pytest

TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tutorials"
NOTEBOOKS = sorted(TUTORIALS_DIR.glob("*.ipynb"))


def test_tutorials_exist():
    assert NOTEBOOKS, "no notebooks found in tutorials/"
    assert len(NOTEBOOKS) >= 4


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_executes_cleanly(path):
    raw = json.loads(path.read_text())
    namespace = {}
    executed = 0
    for cell in raw["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        try:
            exec(compile(source, f"{path.name}:cell{executed}", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001 - surface any cell failure
            pytest.fail(f"{path.name} cell {executed} failed: "
                        f"{type(exc).__name__}: {exc}\n--- source ---\n{source}")
        executed += 1
    assert executed > 0, f"{path.name} contains no executable cells"
