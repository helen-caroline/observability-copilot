from abc import ABC, abstractmethod
from typing import List

from obscopilot.analysis import MetricStats
from obscopilot.deploys import DeployEvent
from obscopilot.models import Insight


class LLMProvider(ABC):
    """Common interface so the CLI doesn't care which LLM API is behind it."""

    @abstractmethod
    def generate_insight(self, stats: MetricStats, deploys: List[DeployEvent]) -> Insight:
        raise NotImplementedError
