"""Event streaming helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable

from reactson.core.events import TaskEvent


def events_to_jsonl(events: Iterable[TaskEvent]) -> str:
    return "".join(f"{json.dumps(event.to_dict(), sort_keys=True)}\n" for event in events)
