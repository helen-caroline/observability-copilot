import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from obscopilot.analysis import compute_stats
from obscopilot.deploys import find_recent_deploys, load_deploys
from obscopilot.llm.anthropic_provider import AnthropicProvider
from obscopilot.llm.base import LLMProvider
from obscopilot.llm.openai_provider import OpenAIProvider
from obscopilot.report import render_insight_text
from obscopilot.sources.prometheus import PrometheusSource


def build_provider(name: str) -> LLMProvider:
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Provider desconhecido: {name!r}")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="obscopilot",
        description=(
            "Consulta métricas do Prometheus, correlaciona com deploys recentes "
            "e resume em português o que está acontecendo."
        ),
    )
    parser.add_argument("target", help="Nome do serviço/pod a investigar (ex: checkout-api)")
    parser.add_argument("--metric", choices=["cpu", "memory"], default="cpu")
    parser.add_argument("--window-minutes", type=int, default=60, help="Janela total analisada (default: 60)")
    parser.add_argument(
        "--recent-minutes", type=int, default=20, help="Quanto do fim da janela é 'período recente' (default: 20)"
    )
    parser.add_argument("--prometheus-url", default=os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090"))
    parser.add_argument("--deploys-file", default=os.getenv("DEPLOYS_FILE", "simulator/deploys.json"))
    parser.add_argument(
        "--provider", choices=["anthropic", "openai"], default=os.getenv("LLM_PROVIDER", "anthropic")
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    load_dotenv()
    args = parse_args(argv)

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=args.window_minutes)
    recent_window = timedelta(minutes=args.recent_minutes)

    source = PrometheusSource(args.prometheus_url)
    samples = source.fetch_series(args.target, args.metric, start, end)
    if not samples:
        print(f"Nenhuma amostra encontrada para '{args.target}' ({args.metric}) na janela analisada.")
        return 1

    stats = compute_stats(samples, target=args.target, metric=args.metric, recent_window=recent_window)

    deploy_events = load_deploys(args.deploys_file)
    correlated = find_recent_deploys(
        deploy_events,
        service=args.target,
        window_start=stats.peak_at - recent_window,
        window_end=end,
    )

    provider = build_provider(args.provider)
    insight = provider.generate_insight(stats, correlated)

    print(render_insight_text(stats, insight))
    return 0


if __name__ == "__main__":
    sys.exit(main())
