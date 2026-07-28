#!/usr/bin/env python3
"""Phase 12/13/14 — Alert notifier for KIX/MIMIR.

Monitors phi-CPS and sends a notification when it stays below threshold
for N consecutive cycles. Supports webhook, email, and Teams channels.
Records notification history and metrics in SQLite. OpenTelemetry traces.
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import sqlite3
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    _tracer = trace.get_tracer(__name__)
except Exception:
    trace = None
    _tracer = None

# Allow import from KIX src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from notification_store import NotificationStore
from notification_metrics import NotificationMetricsStore


DEFAULT_KIX_URL = "http://localhost:8800"
DEFAULT_MIMIR_DB = str(Path(__file__).resolve().parent.parent / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db")
DEFAULT_NOTIFICATIONS_DB = str(Path(__file__).resolve().parent.parent / "data" / "notifications.db")
DEFAULT_INTERVAL = 5
DEFAULT_THRESHOLD = 0.9
DEFAULT_CYCLES = 3


def fetch_alerts(base_url: str, service: str | None = None) -> dict[str, Any]:
    if requests is None:
        raise RuntimeError("requests is required")
    url = f"{base_url}/alerts"
    params = {}
    if service:
        params["service"] = service
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_webhook(payload: dict[str, Any], webhook_url: str | None, metrics_store: NotificationMetricsStore | None = None) -> None:
    if webhook_url:
        if requests is None:
            raise RuntimeError("requests is required for webhook notifications")
        start = time.time()
        try:
            requests.post(webhook_url, json=payload, timeout=10)
            latency = (time.time() - start) * 1000
            if metrics_store:
                metrics_store.record_send("webhook", True, latency)
        except Exception:
            latency = (time.time() - start) * 1000
            if metrics_store:
                metrics_store.record_send("webhook", False, latency)
            raise


def send_email(payload: dict[str, Any], smtp_host: str, smtp_port: int, smtp_user: str | None, smtp_password: str | None, from_addr: str, to_addrs: list[str], metrics_store: NotificationMetricsStore | None = None) -> None:
    subject = f"[KIX ALERT] φ-CPS degraded: {payload.get('phi_cps')} (threshold: {payload.get('threshold')})"
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    start = time.time()
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        latency = (time.time() - start) * 1000
        if metrics_store:
            metrics_store.record_send("email", True, latency)
    except Exception:
        latency = (time.time() - start) * 1000
        if metrics_store:
            metrics_store.record_send("email", False, latency)
        raise


def send_teams(payload: dict[str, Any], webhook_url: str, metrics_store: NotificationMetricsStore | None = None) -> None:
    if requests is None:
        raise RuntimeError("requests is required for Teams notifications")
    text = f"**KIX Alert**: φ-CPS degraded to {payload.get('phi_cps')} (threshold: {payload.get('threshold')})\nService: {payload.get('service') or 'global'}\nConsecutive cycles: {payload.get('consecutive_cycles')}"
    teams_payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "KIX Alert",
        "sections": [
            {
                "activityTitle": "KIX Alert - φ-CPS Degraded",
                "activitySubtitle": payload.get("timestamp"),
                "text": text,
            }
        ],
    }
    start = time.time()
    try:
        requests.post(webhook_url, json=teams_payload, timeout=10)
        latency = (time.time() - start) * 1000
        if metrics_store:
            metrics_store.record_send("teams", True, latency)
    except Exception:
        latency = (time.time() - start) * 1000
        if metrics_store:
            metrics_store.record_send("teams", False, latency)
        raise


def record_notification(notifications_db: str, payload: dict[str, Any], channel: str) -> None:
    store = NotificationStore(notifications_db)
    store.insert(
        event=payload.get("event", "phi_cps_degraded"),
        timestamp=payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
        phi_cps=float(payload.get("phi_cps", 0.0)),
        threshold=float(payload.get("threshold", 0.9)),
        consecutive_cycles=int(payload.get("consecutive_cycles", 1)),
        service=payload.get("service"),
        channel=channel,
        payload=payload,
    )


def monitor(
    kix_url: str,
    mimir_db: str,
    notifications_db: str,
    metrics_db: str,
    interval: int,
    threshold: float,
    cycles: int,
    dry_run: bool,
    webhook_url: str | None = None,
    email_to: list[str] | None = None,
    smtp_host: str | None = None,
    smtp_port: int = 587,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
    email_from: str | None = None,
    teams_webhook: str | None = None,
    service: str | None = None,
) -> int:
    consecutive = 0
    channels = []
    if webhook_url:
        channels.append(("webhook", webhook_url))
    if teams_webhook:
        channels.append(("teams", teams_webhook))
    if email_to and smtp_host:
        channels.append(("email", None))
    metrics_store = NotificationMetricsStore(metrics_db)
    print(f"[alert_notifier] Monitoring {kix_url}/alerts | threshold={threshold} | cycles={cycles} | interval={interval}s | dry_run={dry_run} | channels={[c[0] for c in channels]}")
    try:
        while True:
            data = fetch_alerts(kix_url, service=service)
            phi_cps = float(data.get("phi_cps", 1.0))
            triggered = bool(data.get("triggered"))
            ts = datetime.fromtimestamp(int(data.get("timestamp", time.time())), tz=timezone.utc).isoformat()
            if triggered:
                consecutive += 1
            else:
                consecutive = 0
            print(f"[alert_notifier] {ts} phi_cps={phi_cps} triggered={triggered} consecutive={consecutive}")
            if consecutive >= cycles:
                payload = {
                    "event": "phi_cps_degraded",
                    "timestamp": ts,
                    "phi_cps": phi_cps,
                    "threshold": threshold,
                    "consecutive_cycles": consecutive,
                    "service": service,
                    "items": data.get("items", []),
                }
                print(json.dumps({"notification": payload}, ensure_ascii=False))
                if not dry_run:
                    for channel_name, channel_url in channels:
                        span = None
                        if _tracer:
                            span = _tracer.start_span(f"notification.send.{channel_name}")
                            span.set_attribute("notification.channel", channel_name)
                            span.set_attribute("notification.service", service or "global")
                            span.set_attribute("notification.phi_cps", phi_cps)
                        try:
                            if channel_name == "webhook":
                                send_webhook(payload, channel_url, metrics_store)
                            elif channel_name == "teams":
                                send_teams(payload, channel_url, metrics_store)
                            elif channel_name == "email":
                                send_email(payload, smtp_host, smtp_port, smtp_user, smtp_password, email_from or smtp_user, email_to, metrics_store)
                            record_notification(notifications_db, payload, channel_name)
                            if span:
                                span.set_status(Status(StatusCode.OK))
                        except Exception as exc:
                            if span:
                                span.set_status(Status(StatusCode.ERROR))
                                span.record_exception(exc)
                            print(f"[alert_notifier] channel {channel_name} failed: {exc}")
                        finally:
                            if span:
                                span.end()
                consecutive = 0
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[alert_notifier] Stopped")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KIX alert notifier")
    parser.add_argument("--kix", default=os.environ.get("KIX_URL", DEFAULT_KIX_URL))
    parser.add_argument("--mimir", default=os.environ.get("MIMIR_DB", DEFAULT_MIMIR_DB))
    parser.add_argument("--notifications-db", default=os.environ.get("KIX_NOTIFICATIONS_DB", DEFAULT_NOTIFICATIONS_DB))
    parser.add_argument("--metrics-db", default=os.environ.get("KIX_METRICS_DB", str(Path(__file__).resolve().parent.parent / "data" / "metrics.db")))
    parser.add_argument("--interval", type=int, default=int(os.environ.get("ALERT_INTERVAL", DEFAULT_INTERVAL)))
    parser.add_argument("--threshold", type=float, default=float(os.environ.get("ALERT_THRESHOLD", DEFAULT_THRESHOLD)))
    parser.add_argument("--cycles", type=int, default=int(os.environ.get("ALERT_CYCLES", DEFAULT_CYCLES)))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--webhook-url", default=os.environ.get("ALERT_WEBHOOK_URL"))
    parser.add_argument("--service", default=None)
    parser.add_argument("--email-to", action="append", default=os.environ.get("ALERT_EMAIL_TO", "").split(",") if os.environ.get("ALERT_EMAIL_TO") else [])
    parser.add_argument("--smtp-host", default=os.environ.get("ALERT_SMTP_HOST"))
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("ALERT_SMTP_PORT", "587")))
    parser.add_argument("--smtp-user", default=os.environ.get("ALERT_SMTP_USER"))
    parser.add_argument("--smtp-password", default=os.environ.get("ALERT_SMTP_PASSWORD"))
    parser.add_argument("--email-from", default=os.environ.get("ALERT_EMAIL_FROM"))
    parser.add_argument("--teams-webhook", default=os.environ.get("ALERT_TEAMS_WEBHOOK"))
    args = parser.parse_args(argv)
    email_to = [addr.strip() for addr in args.email_to if addr.strip()] or None
    return monitor(
        args.kix,
        args.mimir,
        args.notifications_db,
        args.metrics_db,
        args.interval,
        args.threshold,
        args.cycles,
        args.dry_run,
        webhook_url=args.webhook_url,
        email_to=email_to,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_password=args.smtp_password,
        email_from=args.email_from,
        teams_webhook=args.teams_webhook,
        service=args.service,
    )


if __name__ == "__main__":
    sys.exit(main())
