from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from obscopilot.sources.base import Sample

ANOMALY_RATIO_THRESHOLD = 1.5
MIN_BASELINE = 1e-6  # avoids division-by-near-zero blowing up the ratio


@dataclass
class MetricStats:
    """Facts computed deterministically from raw samples — this is the only
    thing the LLM ever sees, never the raw time series. The LLM narrates
    these numbers; it never gets to invent or recompute them."""

    target: str
    metric: str
    window_start: datetime
    window_end: datetime
    baseline_avg: float
    peak_value: float
    peak_at: datetime
    current_value: float
    peak_ratio: float
    is_anomalous: bool


def compute_stats(samples: List[Sample], target: str, metric: str, recent_window: timedelta) -> MetricStats:
    if not samples:
        raise ValueError("Sem amostras para calcular estatísticas.")

    ordered = sorted(samples, key=lambda s: s.timestamp)
    window_start, window_end = ordered[0].timestamp, ordered[-1].timestamp
    recent_cutoff = window_end - recent_window

    baseline_samples = [s for s in ordered if s.timestamp < recent_cutoff]
    recent_samples = [s for s in ordered if s.timestamp >= recent_cutoff]

    # If the whole window is shorter than recent_window there's no separate
    # baseline — fall back to comparing the first half against the second.
    if not baseline_samples or not recent_samples:
        midpoint = max(len(ordered) // 2, 1)
        baseline_samples = ordered[:midpoint]
        recent_samples = ordered[midpoint:] or ordered[-1:]

    baseline_avg = sum(s.value for s in baseline_samples) / len(baseline_samples)
    peak_sample = max(recent_samples, key=lambda s: s.value)

    if baseline_avg < MIN_BASELINE:
        peak_ratio = float("inf") if peak_sample.value > MIN_BASELINE else 1.0
        is_anomalous = peak_sample.value > MIN_BASELINE * 100
    else:
        peak_ratio = peak_sample.value / baseline_avg
        is_anomalous = peak_ratio >= ANOMALY_RATIO_THRESHOLD

    return MetricStats(
        target=target,
        metric=metric,
        window_start=window_start,
        window_end=window_end,
        baseline_avg=baseline_avg,
        peak_value=peak_sample.value,
        peak_at=peak_sample.timestamp,
        current_value=ordered[-1].value,
        peak_ratio=peak_ratio,
        is_anomalous=is_anomalous,
    )
