import json
import os
from typing import List

from openai import OpenAI

from obscopilot.analysis import MetricStats
from obscopilot.deploys import DeployEvent
from obscopilot.facts import format_facts
from obscopilot.llm.base import LLMProvider
from obscopilot.models import Insight
from obscopilot.prompt import SYSTEM_PROMPT

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    def generate_insight(self, stats: MetricStats, deploys: List[DeployEvent]) -> Insight:
        schema_hint = json.dumps(Insight.model_json_schema(), ensure_ascii=False)
        system = (
            f"{SYSTEM_PROMPT}\n\n"
            "Responda SOMENTE com um JSON válido (sem markdown, sem texto extra) "
            f"seguindo exatamente este schema:\n{schema_hint}"
        )
        completion = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": format_facts(stats, deploys)},
            ],
        )
        raw = completion.choices[0].message.content
        return Insight.model_validate(json.loads(raw))
