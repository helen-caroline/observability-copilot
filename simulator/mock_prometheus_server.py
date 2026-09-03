"""A tiny fake Prometheus that speaks its query_range HTTP API.

Not a real TSDB — it always synthesizes a series for whatever [start, end,
step] window is requested, injecting a CPU spike in the last ANOMALY_MINUTES
of that window and a flat memory series (no anomaly) — good enough to
demonstrate the full pipeline (fetch -> analyze -> correlate -> LLM summary)
end-to-end without needing a real cluster.
"""

import argparse
import http.server
import json
import random
import socketserver
import urllib.parse

ANOMALY_MINUTES = 20
BASELINE_CPU = 0.15  # cores
SPIKE_CPU = 0.85  # cores during the simulated incident
BASELINE_MEMORY = 250_000_000  # bytes
NOISE_RATIO = 0.05


def generate_series(start: float, end: float, step: float, metric: str):
    points = []
    anomaly_cutoff = end - ANOMALY_MINUTES * 60
    t = start
    while t <= end:
        if metric == "cpu":
            base = SPIKE_CPU if t >= anomaly_cutoff else BASELINE_CPU
        else:
            base = BASELINE_MEMORY
        noise = base * NOISE_RATIO * (random.random() * 2 - 1)
        points.append([t, f"{base + noise:.6f}"])
        t += step
    return points


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/v1/query_range":
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("query", [""])[0]
        start = float(params.get("start", ["0"])[0])
        end = float(params.get("end", ["0"])[0])
        step = float(params.get("step", ["15s"])[0].rstrip("s"))

        metric = "memory" if "memory" in query else "cpu"
        values = generate_series(start, end, step, metric)

        body = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [{"metric": {"pod": "demo-pod"}, "values": values}] if values else [],
            },
        }
        payload = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # keep the demo terminal quiet


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def serve(host: str, port: int) -> None:
    with Server((host, port), Handler) as httpd:
        print(f"Mock Prometheus ouvindo em http://{host}:{port}")
        print(f"Simulando um pico de CPU nos últimos {ANOMALY_MINUTES} minutos de qualquer janela consultada.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nEncerrando simulador.")


def parse_args():
    parser = argparse.ArgumentParser(description="Simulador da API de query_range do Prometheus (para demo/testes).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9090)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    serve(args.host, args.port)
