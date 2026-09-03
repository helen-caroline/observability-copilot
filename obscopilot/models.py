from typing import Literal, Optional

from pydantic import BaseModel, Field


class Insight(BaseModel):
    """Structured output the LLM must return: a narrative on top of facts the
    code already computed — the LLM never invents the numbers themselves."""

    summary: str = Field(
        ...,
        description=(
            "Resumo em 2-3 frases, em português simples, do que está acontecendo "
            "(ex: 'CPU alta há 20min no pod X, correlacionado com o deploy da v1.8.2')."
        ),
    )
    severity: Literal["info", "warning", "critical"] = Field(
        ..., description="Severidade da situação, considerando a anomalia e a correlação encontrada."
    )
    likely_cause: Optional[str] = Field(
        default=None, description="Causa provável, se houver um deploy correlacionado ou outro indício claro."
    )
    recommended_action: str = Field(
        ..., description="Próximo passo sugerido (ex: 'considerar rollback', 'monitorar mais 10min', 'nada a fazer')."
    )
