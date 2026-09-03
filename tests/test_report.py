from datetime import datetime, timezone

from obscopilot.analysis import MetricStats
from obscopilot.models import Insight
from obscopilot.report import render_insight_text

STATS = MetricStats(
    target="checkout-api",
    metric="cpu",
    window_start=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    window_end=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
    baseline_avg=0.15,
    peak_value=0.85,
    peak_at=datetime(2026, 1, 1, 10, 45, tzinfo=timezone.utc),
    current_value=0.83,
    peak_ratio=5.67,
    is_anomalous=True,
)


def test_render_includes_severity_summary_and_action():
    insight = Insight(
        summary="CPU alta há 15min no checkout-api, correlacionado com o deploy da v1.8.2.",
        severity="critical",
        likely_cause="Deploy da v1.8.2 há 22 minutos.",
        recommended_action="Considerar rollback para a v1.8.1.",
    )
    text = render_insight_text(STATS, insight)

    assert "CRITICAL" in text
    assert "checkout-api" in text
    assert "5.67x" in text
    assert "Causa provável" in text
    assert "rollback" in text


def test_render_without_likely_cause():
    insight = Insight(
        summary="CPU alta, sem deploy correlacionado encontrado.",
        severity="warning",
        likely_cause=None,
        recommended_action="Monitorar por mais 10-15min.",
    )
    text = render_insight_text(STATS, insight)

    assert "Causa provável" not in text
    assert "Monitorar" in text
