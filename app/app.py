"""Simple Python logging demo for the EFK stack.

Uses only the standard library `logging` module. Every record is written to
stdout as one JSON line; Docker's fluentd log driver ships it to Fluentd.
"""
import json
import logging
import os
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timezone

SERVICE_NAME = os.getenv("SERVICE_NAME", "python-demo")
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_INTERVAL = float(os.getenv("LOG_INTERVAL", "1.0"))

# Attributes present on every LogRecord; anything else came from `extra={...}`
_STD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "env": APP_ENV,
        }
        # Custom structured fields passed through extra={...}
        payload.update({k: v for k, v in record.__dict__.items() if k not in _STD_ATTRS})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(LOG_LEVEL)


log = logging.getLogger("demo.app")
_running = True


def _stop(*_):
    global _running
    _running = False


def simulate_request():
    ctx = {
        "request_id": uuid.uuid4().hex[:12],
        "user_id": random.randint(1, 50),
        "endpoint": random.choice(["/login", "/orders", "/payments", "/search", "/profile"]),
        "duration_ms": round(random.expovariate(1 / 120), 1),
    }
    roll = random.random()
    if roll < 0.60:
        log.info("request completed", extra={**ctx, "status": 200})
    elif roll < 0.75:
        log.debug("cache miss, hitting database", extra=ctx)
    elif roll < 0.88:
        log.warning("slow request detected", extra={**ctx, "duration_ms": ctx["duration_ms"] + 800, "status": 200})
    elif roll < 0.95:
        log.error("payment declined", extra={**ctx, "status": 402, "reason": "insufficient_funds"})
    else:
        try:
            _ = {"a": 1}["missing_key"]
        except KeyError:
            log.exception("unhandled error while processing request", extra={**ctx, "status": 500})


def main():
    setup_logging()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log.info("service started", extra={"log_level": LOG_LEVEL, "interval_s": LOG_INTERVAL})
    while _running:
        simulate_request()
        time.sleep(LOG_INTERVAL)
    log.info("service stopped")


if __name__ == "__main__":
    main()
