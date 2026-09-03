from typing import List

from obscopilot.analysis import MetricStats
from obscopilot.deploys import DeployEvent


def format_facts(stats: MetricStats, deploys: List[DeployEvent]) -> str:
    """Render the computed stats + correlated deploys as plain text for the
    LLM prompt. The LLM only ever sees this — never the raw time series."""
    lines = [
        f"Alvo: {stats.target}",
        f"Métrica: {stats.metric}",
        f"Janela analisada: {stats.window_start.isoformat()} até {stats.window_end.isoformat()}",
        f"Baseline (média antes do período recente): {stats.baseline_avg:.4f}",
        f"Pico no período recente: {stats.peak_value:.4f} (em {stats.peak_at.isoformat()})",
        f"Valor atual (última amostra): {stats.current_value:.4f}",
        f"Razão pico/baseline: {stats.peak_ratio:.2f}x",
        f"Anomalia detectada pelo código (razão >= {1.5}x): {'SIM' if stats.is_anomalous else 'NÃO'}",
    ]
    if deploys:
        lines.append("Deploys do mesmo serviço dentro/perto da janela analisada:")
        for d in deploys:
            lines.append(f"  - {d.service} v{d.version} em {d.timestamp.isoformat()}")
    else:
        lines.append("Nenhum deploy do serviço encontrado dentro/perto da janela analisada.")
    return "\n".join(lines)
