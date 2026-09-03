import os
from typing import List

import anthropic

from obscopilot.analysis import MetricStats
from obscopilot.deploys import DeployEvent
from obscopilot.facts import format_facts
from obscopilot.llm.base import LLMProvider
from obscopilot.models import Insight
from obscopilot.prompt import SYSTEM_PROMPT

DEFAULT_MODEL = "claude-opus-5"


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    def generate_insight(self, stats: MetricStats, deploys: List[DeployEvent]) -> Insight:
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": format_facts(stats, deploys)}],
            output_format=Insight,
        )
        return response.parsed_output
