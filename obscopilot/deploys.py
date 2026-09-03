import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class DeployEvent:
    service: str
    version: str
    timestamp: datetime


def load_deploys(path: str) -> List[DeployEvent]:
    if not Path(path).exists():
        return []
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        DeployEvent(
            service=item["service"],
            version=item["version"],
            timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
        )
        for item in raw
    ]


def find_recent_deploys(
    events: List[DeployEvent], service: str, window_start: datetime, window_end: datetime
) -> List[DeployEvent]:
    matches = [e for e in events if e.service == service and window_start <= e.timestamp <= window_end]
    return sorted(matches, key=lambda e: e.timestamp)
