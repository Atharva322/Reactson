from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from reactson.engineering import RepositoryDiagnosisAgent, RepositoryTools


def test_repository_tools_list_and_search_files() -> None:
    root = _workspace_tmp()
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("raise ImportError('missing package')\n", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "ignored.py").write_text("ImportError\n", encoding="utf-8")

    tools = RepositoryTools(root)

    assert tools.list_files("*.py") == ("tests/test_demo.py",)
    matches = tools.search("ImportError", "*.py")
    assert len(matches) == 1
    assert matches[0].path == "tests/test_demo.py"
    assert matches[0].line == 1


def test_repository_diagnosis_agent_produces_evidence_backed_report() -> None:
    root = _workspace_tmp()
    (root / "tests").mkdir()
    (root / "tests" / "test_imports.py").write_text("raise ImportError('bad dependency')\n", encoding="utf-8")

    report = RepositoryDiagnosisAgent.from_path(root).diagnose("Find why tests fail")

    assert report.objective == "Find why tests fail"
    assert report.metadata["agent"] == "repository_diagnosis"
    assert report.metadata["evidence_count"] >= 2
    assert report.hypotheses[0].confidence == 0.85
    assert "dependency or import compatibility" in report.summary
    assert report.recommended_next_steps


def _workspace_tmp() -> Path:
    root = Path(".test-artifacts") / str(uuid4())
    root.mkdir(parents=True, exist_ok=True)
    return root
