# tests/test_tutorials.py
"""Tutorials cannot rot: every code cell of every notebook in tutorials/
is executed top-to-bottom. Any exception fails the suite."""
import json
import pathlib
import re

import pytest
from qvm.parser import OpenQASM2Parser
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator

TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tutorials"
NOTEBOOKS = sorted(TUTORIALS_DIR.glob("*.ipynb"))
MARKDOWN_TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[1] / "docs" / "tutorials"
WEB_TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[1] / "web" / "docs-content"
MARKDOWN_TUTORIALS = [
    *sorted(MARKDOWN_TUTORIALS_DIR.glob("*.md")),
    *sorted(WEB_TUTORIALS_DIR.glob("7*.md")),
]
FENCED_BLOCK = re.compile(
    r"^```(?P<language>python|qasm)\s*\r?$\n(?P<source>.*?)(?=^```\s*$)",
    re.MULTILINE | re.DOTALL,
)


def _markdown_tutorial_snippets():
    for path in MARKDOWN_TUTORIALS:
        source_text = path.read_text(encoding="utf-8")
        for block_index, match in enumerate(FENCED_BLOCK.finditer(source_text), start=1):
            language = match["language"]
            source = match["source"]
            if language == "qasm" and not source.lstrip().startswith("OPENQASM"):
                continue
            if language == "python" and not re.search(
                r"^(?:from\s+\S+\s+import|import\s+\S+)", source, re.MULTILINE
            ):
                continue
            yield path, language, block_index, source


def _parse_and_simulate_qasm(source):
    if source.lstrip().startswith("OPENQASM 3"):
        circuit = OpenQASM3Parser().parse(source)
    else:
        circuit = OpenQASM2Parser.parse(source)
    Simulator().simulate(circuit)


MARKDOWN_SNIPPETS = list(_markdown_tutorial_snippets())
MARKDOWN_TUTORIAL_PARAMETERS = [
    pytest.param(
        path,
        tuple(snippet for snippet in MARKDOWN_SNIPPETS if snippet[0] == path),
        id=path.name,
    )
    for path in dict.fromkeys(path for path, _, _, _ in MARKDOWN_SNIPPETS)
]


def test_tutorials_exist():
    assert NOTEBOOKS, "no notebooks found in tutorials/"
    assert len(NOTEBOOKS) >= 4


def test_markdown_tutorial_snippets_are_collected():
    assert MARKDOWN_SNIPPETS, "no executable Markdown tutorial snippets found"
    assert {language for _, language, _, _ in MARKDOWN_SNIPPETS} == {"python", "qasm"}
    assert all(source.strip() for _, _, _, source in MARKDOWN_SNIPPETS)
    assert {path.parent for path, _, _, _ in MARKDOWN_SNIPPETS} == {
        MARKDOWN_TUTORIALS_DIR,
        WEB_TUTORIALS_DIR,
    }


@pytest.mark.parametrize(
    "path, snippets",
    MARKDOWN_TUTORIAL_PARAMETERS,
)
def test_markdown_tutorial_snippets_execute_cleanly(path, snippets):
    namespace = {}
    for _, language, block_index, source in snippets:
        try:
            if language == "qasm":
                _parse_and_simulate_qasm(source)
            else:
                exec(compile(source, f"{path.name}:block{block_index}", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001 - surface any block failure
            pytest.fail(
                f"{path.name} block {block_index} ({language}) failed: "
                f"{type(exc).__name__}: {exc}\n--- source ---\n{source}"
            )


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
