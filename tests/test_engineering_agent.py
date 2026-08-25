from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from reactson.engineering import PatchProposalGenerator, RepositoryDiagnosisAgent, RepositoryTools, SafeTestRunner
from reactson.epistemic import EpistemicEngine, ExecutionMemory


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


def test_safe_test_runner_parses_failure_output() -> None:
    runner = SafeTestRunner(executor=_fake_pytest_failure)

    result = runner.run(("pytest", "-q"))

    assert result.success is False
    evidence = result.evidence()
    assert evidence[0].source == "test_output"
    assert evidence[0].path == "tests/test_demo.py"
    assert evidence[0].line == 12


def test_safe_test_runner_rejects_unapproved_commands() -> None:
    runner = SafeTestRunner(executor=_fake_pytest_failure)

    try:
        runner.run(("rm", "-rf", "."))
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("unsafe command should be rejected")


def test_agent_uses_test_output_and_failure_memory() -> None:
    root = _workspace_tmp()
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("def test_demo(): pass\n", encoding="utf-8")
    memory = EpistemicEngine()
    memory.remember_episode(
        ExecutionMemory(task_id="task-a", text="Prior failure: ImportError from enum compatibility")
    )
    agent = RepositoryDiagnosisAgent(
        RepositoryTools(root),
        test_runner=SafeTestRunner(executor=_fake_pytest_failure),
        memory=memory,
        task_id="task-a",
    )

    report = agent.diagnose("Find failing test cause", run_tests=True)

    assert report.metadata["test_exit_code"] == 1
    assert any(item.source == "failure_memory" for item in report.evidence)
    assert any(item.source == "test_output" for item in report.evidence)
    assert report.hypotheses[0].confidence >= 0.75


def test_report_final_answer_is_evidence_backed() -> None:
    root = _workspace_tmp()
    (root / "tests").mkdir()
    (root / "tests" / "test_imports.py").write_text("raise ImportError('bad dependency')\n", encoding="utf-8")

    report = RepositoryDiagnosisAgent.from_path(root).diagnose("Explain failure")
    answer = report.final_answer()

    assert "Top hypothesis" in answer
    assert "Evidence:" in answer
    assert "tests/test_imports.py" in answer


def test_patch_proposal_is_non_destructive() -> None:
    root = _workspace_tmp()
    (root / "tests").mkdir()
    (root / "tests" / "test_imports.py").write_text("raise ImportError('bad dependency')\n", encoding="utf-8")

    report = RepositoryDiagnosisAgent.from_path(root).diagnose("Suggest patch")
    proposal = PatchProposalGenerator().propose(report)

    assert proposal.destructive is False
    assert proposal.suggestions
    assert proposal.suggestions[0].path == "tests/test_imports.py"
    assert "dependency" in proposal.suggestions[0].proposed_change.lower()


def _workspace_tmp() -> Path:
    root = Path(".test-artifacts") / str(uuid4())
    root.mkdir(parents=True, exist_ok=True)
    return root


def _fake_pytest_failure(command, timeout_seconds):
    return (
        1,
        "FAILED tests/test_demo.py:12 - AssertionError: expected ok\n",
        "",
    )
