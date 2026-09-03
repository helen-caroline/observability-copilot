from datetime import datetime, timezone
from typing import Dict, List

import requests

from obscopilot.sources.base import MetricsSource, Sample

# PromQL templates per logical metric name. {target} is expected to be a
# service/deployment name; "=~" + ".*" matches all pod replicas of it, since
# a real deployment usually has several pods sharing that name prefix.
METRIC_QUERIES: Dict[str, str] = {
    "cpu": 'rate(container_cpu_usage_seconds_total{{pod=~"{target}.*"}}[5m])',
    "memory": 'container_memory_usage_bytes{{pod=~"{target}.*"}}',
}


class PrometheusSource(MetricsSource):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def fetch_series(
        self, target: str, metric: str, start: datetime, end: datetime, step_seconds: int = 15
    ) -> List[Sample]:
        query_template = METRIC_QUERIES.get(metric)
        if query_template is None:
            raise ValueError(f"Métrica desconhecida: {metric!r}. Opções: {', '.join(METRIC_QUERIES)}")

        query = query_template.format(target=target)
        response = requests.get(
            f"{self.base_url}/api/v1/query_range",
            params={
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": f"{step_seconds}s",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(f"Prometheus retornou erro: {payload}")

        result = payload["data"]["result"]
        if not result:
            return []

        # Soma os valores de todas as séries retornadas (ex: várias réplicas
        # do mesmo serviço) alinhadas por timestamp — reflete como você
        # normalmente lê CPU/memória agregada de um deployment inteiro.
        merged: Dict[float, float] = {}
        for series in result:
            for ts, value in series["values"]:
                merged[ts] = merged.get(ts, 0.0) + float(value)

        return [
            Sample(timestamp=datetime.fromtimestamp(ts, tz=timezone.utc), value=v)
            for ts, v in sorted(merged.items())
        ]
