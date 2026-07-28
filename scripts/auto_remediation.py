#!/usr/bin/env python3
"""Phase 15 — Auto-remediation engine for KIX/MIMIR.

Reads policies from config/automation.yaml and executes actions
when conditions are met.

Usage:
    python scripts/auto_remediation.py --kix http://localhost:8800 --dry-run
    python scripts/auto_remediation.py --service RLM-GRAPH --action restart
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
import yaml

# Allow import from KIX src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from auto_remediation import RemediationStore, RemediationResult
from notification_store import NotificationStore
from notification_metrics import NotificationMetricsStore


DEFAULT_KIX_URL = "http://localhost:8800"
DEFAULT_AUTOMATION_CONFIG = str(Path(__file__).resolve().parent.parent / "config" / "automation.yaml")
DEFAULT_NOTIFICATIONS_DB = str(Path(__file__).resolve().parent.parent / "data" / "notifications.db")
DEFAULT_METRICS_DB = str(Path(__file__).resolve().parent.parent / "data" / "metrics.db")
DEFAULT_INTERVAL = 10


def load_policies(config_path: str) -> list[dict[str, Any]]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    policies = data.get("policies", [])
    return [p for p in policies if p.get("enabled", True)]


def evaluate_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    field = condition.get("field", "")
    operator = condition.get("operator", "==")
    value = condition.get("value")
    actual = context.get(field)
    if operator == "==":
        return actual == value
    if operator == "!=":
        return actual != value
    if operator == "<":
        try:
            return float(actual or 0) < float(value)
        except (TypeError, ValueError):
            return False
    if operator == ">":
        try:
            return float(actual or 0) > float(value)
        except (TypeError, ValueError):
            return False
    if operator == ">=":
        try:
            return float(actual or 0) >= float(value)
        except (TypeError, ValueError):
            return False
    if operator == "<=":
        try:
            return float(actual or 0) <= float(value)
        except (TypeError, ValueError):
            return False
    return False


def execute_restart_runner(kix_url: str, runner_name: str, dry_run: bool, params: dict[str, Any]) -> tuple[bool, str]:
    delay = params.get("delay_seconds", 0)
    if delay > 0 and not dry_run:
        time.sleep(delay)
    if dry_run:
        return True, f"dry-run: would restart {runner_name}"
    try:
        resp = requests.post(f"{kix_url}/runners/{runner_name}/start", timeout=30)
        if resp.status_code == 200:
            return True, f"restart triggered for {runner_name}"
        return False, f"failed to restart {runner_name}: {resp.status_code} {resp.text}"
    except Exception as exc:
        return False, f"error restarting {runner_name}: {exc}"


def execute_send_notification(payload: dict[str, Any], dry_run: bool, notifications_db: str, metrics_db: str) -> tuple[bool, str]:
    channels = payload.get("channels", [])
    if not channels:
        return True, "no channels configured"
    if dry_run:
        return True, f"dry-run: would send notification via {channels}"
    try:
        notifications = NotificationStore(notifications_db)
        metrics = NotificationMetricsStore(metrics_db)
        success = True
        details = []
        for channel in channels:
            try:
                if channel == "webhook":
                    from scripts.alert_notifier import send_webhook
                    send_webhook(payload, os.environ.get("ALERT_WEBHOOK_URL"), metrics)
                elif channel == "teams":
                    from scripts.alert_notifier import send_teams
                    send_teams(payload, os.environ.get("ALERT_TEAMS_WEBHOOK"), metrics)
                elif channel == "email":
                    from scripts.alert_notifier import send_email
                    smtp_host = os.environ.get("ALERT_SMTP_HOST")
                    if smtp_host:
                        email_to = [addr.strip() for addr in os.environ.get("ALERT_EMAIL_TO", "").split(",") if addr.strip()]
                        send_email(
                            payload,
                            smtp_host,
                            int(os.environ.get("ALERT_SMTP_PORT", "587")),
                            os.environ.get("ALERT_SMTP_USER"),
                            os.environ.get("ALERT_SMTP_PASSWORD"),
                            os.environ.get("ALERT_EMAIL_FROM", os.environ.get("ALERT_SMTP_USER", "")),
                            email_to,
                            metrics,
                        )
                notifications.insert(
                    event=payload.get("event", "remediation"),
                    timestamp=payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    phi_cps=float(payload.get("phi_cps", 0.0)),
                    threshold=float(payload.get("threshold", 0.9)),
                    consecutive_cycles=int(payload.get("consecutive_cycles", 1)),
                    service=payload.get("service"),
                    channel=channel,
                    payload=payload,
                )
                details.append(f"{channel}: sent")
            except Exception as exc:
                success = False
                details.append(f"{channel}: failed ({exc})")
        return success, "; ".join(details)
    except Exception as exc:
        return False, f"notification error: {exc}"


def execute_action(action_type: str, params: dict[str, Any], context: dict[str, Any], dry_run: bool, kix_url: str, notifications_db: str, metrics_db: str) -> tuple[bool, str]:
    if action_type == "restart_runner":
        service = context.get("runner_name") or context.get("service")
        if not service:
            return False, "missing service name for restart"
        return execute_restart_runner(kix_url, service, dry_run, params)
    if action_type == "send_notification":
        payload = dict(params.get("message", {})) if isinstance(params.get("message"), dict) else {"message": str(params.get("message", ""))}
        payload.update(context)
        return execute_send_notification(payload, dry_run, notifications_db, metrics_db)
    return False, f"unknown action type: {action_type}"


def remediate(kix_url: str, config_path: str, notifications_db: str, metrics_db: str, dry_run: bool, service_filter: Optional[str] = None) -> list[RemediationResult]:
    policies = load_policies(config_path)
    results: list[RemediationResult] = []
    try:
        alerts_resp = requests.get(f"{kix_url}/alerts", timeout=30)
        alerts_resp.raise_for_status()
        alerts_data = alerts_resp.json()
    except Exception as exc:
        print(f"[auto_remediation] failed to fetch alerts: {exc}")
        return results
    items = alerts_data.get("items", [])
    if not items:
        print("[auto_remediation] no unhealthy items")
        return results
    for item in items:
        service_name = item.get("name")
        if service_filter and service_name != service_filter:
            continue
        context = {
            "runner_name": service_name,
            "service": service_name,
            "runner_status": item.get("status"),
            "phi_cps": alerts_data.get("phi_cps"),
            "threshold": alerts_data.get("threshold"),
            "consecutive_failures": 1,
        }
        for policy in policies:
            condition = policy.get("condition", {})
            if not evaluate_condition(condition, context):
                continue
            action = policy.get("action", {})
            action_type = action.get("type", "")
            params = action.get("params", {})
            print(f"[auto_remediation] policy={policy['id']} service={service_name} action={action_type} dry_run={dry_run}")
            success, detail = execute_action(action_type, params, context, dry_run, kix_url, notifications_db, metrics_db)
            result = RemediationResult(
                policy_id=policy["id"],
                service=service_name,
                action_type=action_type,
                success=success,
                detail=detail,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            results.append(result)
            print(f"[auto_remediation] result success={success} detail={detail}")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KIX auto-remediation engine")
    parser.add_argument("--kix", default=os.environ.get("KIX_URL", DEFAULT_KIX_URL))
    parser.add_argument("--config", default=os.environ.get("AUTOMATION_CONFIG", DEFAULT_AUTOMATION_CONFIG))
    parser.add_argument("--notifications-db", default=os.environ.get("KIX_NOTIFICATIONS_DB", DEFAULT_NOTIFICATIONS_DB))
    parser.add_argument("--metrics-db", default=os.environ.get("KIX_METRICS_DB", DEFAULT_METRICS_DB))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--service", default=None)
    parser.add_argument("--action", default=None, choices=["restart", "notify", "all"])
    parser.add_argument("--interval", type=int, default=int(os.environ.get("REMEDIATION_INTERVAL", DEFAULT_INTERVAL)))
    args = parser.parse_args(argv)
    store = RemediationStore(args.config.replace("automation.yaml", "remediation.db") if "automation.yaml" in args.config else str(Path(args.config).parent / "remediation.db"))
    try:
        while True:
            results = remediate(args.kix, args.config, args.notifications_db, args.metrics_db, args.dry_run, args.service)
            for result in results:
                store.record(result)
            if args.action is not None:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[auto_remediation] Stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
