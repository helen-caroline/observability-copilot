from datetime import datetime, timedelta, timezone

from obscopilot.analysis import compute_stats
from obscopilot.sources.base import Sample

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _series(baseline: float, spike: float, total_minutes: int, spike_minutes: int, step_seconds: int = 60):
    samples = []
    total_points = (total_minutes * 60) // step_seconds
    spike_points = (spike_minutes * 60) // step_seconds
    for i in range(total_points):
        t = BASE_TIME + timedelta(seconds=i * step_seconds)
        value = spike if i >= total_points - spike_points else baseline
        samples.append(Sample(timestamp=t, value=value))
    return samples


def test_detects_a_clear_spike():
    samples = _series(baseline=0.15, spike=0.85, total_minutes=60, spike_minutes=20)
    stats = compute_stats(samples, target="checkout-api", metric="cpu", recent_window=timedelta(minutes=20))

    assert stats.is_anomalous is True
    assert stats.peak_value == 0.85
    assert stats.peak_ratio > 1.5


def test_flat_series_is_not_anomalous():
    samples = _series(baseline=0.15, spike=0.15, total_minutes=60, spike_minutes=20)
    stats = compute_stats(samples, target="checkout-api", metric="cpu", recent_window=timedelta(minutes=20))

    assert stats.is_anomalous is False
    assert stats.peak_ratio == 1.0


def test_near_zero_baseline_does_not_blow_up_the_ratio():
    samples = _series(baseline=0.0, spike=0.0, total_minutes=30, spike_minutes=10)
    stats = compute_stats(samples, target="idle-service", metric="cpu", recent_window=timedelta(minutes=10))

    assert stats.is_anomalous is False
    assert stats.peak_ratio == 1.0


def test_window_shorter_than_recent_falls_back_to_first_half_as_baseline():
    # 10 points total; recent_window (20min) is longer than the whole window
    # (10min at this step), so there's no "before the recent cutoff" segment
    # — compute_stats must fall back to first-half-vs-second-half instead.
    samples = [Sample(timestamp=BASE_TIME + timedelta(minutes=i), value=0.1 if i < 5 else 0.5) for i in range(10)]
    stats = compute_stats(samples, target="checkout-api", metric="cpu", recent_window=timedelta(minutes=20))

    assert stats.baseline_avg < stats.peak_value
