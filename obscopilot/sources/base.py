from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Sample:
    timestamp: datetime
    value: float


class MetricsSource(ABC):
    """Common interface so the CLI doesn't care which observability backend
    is behind it (Prometheus today; Zabbix/ELK could implement this later)."""

    @abstractmethod
    def fetch_series(
        self, target: str, metric: str, start: datetime, end: datetime, step_seconds: int = 15
    ) -> List[Sample]:
        raise NotImplementedError
