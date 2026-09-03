from obscopilot.analysis import MetricStats
from obscopilot.models import Insight

SEVERITY_EMOJI = {"info": "🟢", "warning": "🟡", "critical": "🔴"}


def render_insight_text(stats: MetricStats, insight: Insight) -> str:
    lines = [
        f"{SEVERITY_EMOJI[insight.severity]} [{insight.severity.upper()}] {stats.target} — métrica: {stats.metric}",
        "",
        insight.summary,
        "",
        (
            f"Pico: {stats.peak_value:.4f} ({stats.peak_ratio:.2f}x a baseline de "
            f"{stats.baseline_avg:.4f}) às {stats.peak_at.strftime('%H:%M:%S UTC')}"
        ),
        f"Anomalia detectada pelo código: {'sim' if stats.is_anomalous else 'não'}",
    ]
    if insight.likely_cause:
        lines.append(f"Causa provável: {insight.likely_cause}")
    lines.append(f"Ação recomendada: {insight.recommended_action}")
    return "\n".join(lines)
