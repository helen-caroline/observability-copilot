import json
from datetime import datetime, timedelta, timezone

from obscopilot.deploys import find_recent_deploys, load_deploys

NOW = datetime.now(timezone.utc)


def test_load_and_filter_by_service_and_window(tmp_path):
    path = tmp_path / "deploys.json"
    path.write_text(
        json.dumps(
            [
                {"service": "checkout-api", "version": "1.8.2", "timestamp": (NOW - timedelta(minutes=22)).isoformat()},
                {"service": "checkout-api", "version": "1.8.1", "timestamp": (NOW - timedelta(days=3)).isoformat()},
                {"service": "other-service", "version": "2.0.0", "timestamp": (NOW - timedelta(minutes=5)).isoformat()},
            ]
        ),
        encoding="utf-8",
    )

    events = load_deploys(str(path))
    assert len(events) == 3

    recent = find_recent_deploys(
        events, service="checkout-api", window_start=NOW - timedelta(minutes=30), window_end=NOW
    )
    assert [e.version for e in recent] == ["1.8.2"]


def test_missing_file_returns_empty_list(tmp_path):
    events = load_deploys(str(tmp_path / "does-not-exist.json"))
    assert events == []
