from __future__ import annotations

import json

import reactson
from reactson.api.app import health_payload
from reactson.cli import main
from reactson.config.settings import ReactsonSettings
from reactson.core.phases import PHASES


def test_import_exposes_version() -> None:
    assert reactson.__version__ == "0.1.0"


def test_settings_use_reactson_environment(monkeypatch) -> None:
    monkeypatch.setenv("REACTSON_ENV", "test")

    settings = ReactsonSettings.from_environment()

    assert settings.environment == "test"
    assert settings.execution_log_dir == "reactson_execution_logs"
    assert settings.tool_schema_dir == "reactson_tool_schemas"
    assert settings.kernel_name == "reactson-kernel"


def test_health_payload_is_reactson_branded() -> None:
    payload = health_payload(ReactsonSettings(environment="test"))

    assert payload == {
        "service": "reactson",
        "status": "ok",
        "version": reactson.__version__,
        "environment": "test",
    }


def test_cli_health_outputs_json(capsys) -> None:
    assert main(["health"]) == 0

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["service"] == "reactson"
    assert payload["status"] == "ok"


def test_phase_tracker_lists_all_roadmap_phases() -> None:
    assert [phase.index for phase in PHASES] == list(range(7))
    assert PHASES[0].status == "completed"
    assert PHASES[1].status == "completed"
    assert PHASES[2].status == "completed"
    assert PHASES[3].status == "completed"
    assert PHASES[4].status == "completed"
    assert PHASES[5].status == "completed"
    assert PHASES[6].status == "completed"
    assert PHASES[-1].name == "Evaluation, Reliability and Release Hardening"
