"""Registra um deploy simulado num log local, pra correlacionar com a
métrica na hora de rodar a demo — usa "agora - N minutos" em vez de uma data
fixa, então o demo continua fazendo sentido não importa quando você rodar.
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def seed(path: str, service: str, version: str, minutes_ago: int) -> None:
    events = []
    if Path(path).exists():
        events = json.loads(Path(path).read_text(encoding="utf-8"))

    timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    events.append({"service": service, "version": version, "timestamp": timestamp.isoformat()})

    Path(path).write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Deploy registrado: {service} v{version}, há {minutes_ago}min ({timestamp.isoformat()}) em {path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Registra um deploy simulado para o Observability Copilot correlacionar.")
    parser.add_argument("--service", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--minutes-ago", type=int, default=22)
    parser.add_argument("--file", default="simulator/deploys.json")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed(args.file, args.service, args.version, args.minutes_ago)
