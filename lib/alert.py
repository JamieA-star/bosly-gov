"""
Bosly Gov alert email.

Sends a short failure alert to the address in Gov's .env (ALERT_EMAIL).
Reads SMTP credentials from Accord's .env.production so there is one
source of truth for outbound email configuration.

Only sends when there is something to say. Silence means everything
passed.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

ACCORD_ENV = Path("/home/bosly_accord/bosly-1.0/.env.production")
GOV_ENV = Path("/home/bosly_accord/bosly-gov/.env")


def _parse_env(path: Path) -> dict:
    """Read a .env file into a dict, stripping quotes and skipping blanks."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        out[k.strip()] = v
    return out


def _load_config() -> dict:
    smtp = _parse_env(ACCORD_ENV)
    gov = _parse_env(GOV_ENV)

    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM"]
    missing = [k for k in required if not smtp.get(k)]
    if missing:
        raise RuntimeError("missing SMTP vars: " + ", ".join(missing))

    recipient = gov.get("ALERT_EMAIL")
    if not recipient:
        raise RuntimeError("ALERT_EMAIL not set in " + str(GOV_ENV))

    return {
        "host": smtp["SMTP_HOST"],
        "port": int(smtp["SMTP_PORT"]),
        "user": smtp["SMTP_USER"],
        "password": smtp["SMTP_PASS"],
        "from": smtp["SMTP_FROM"],
        "to": recipient,
        "secure": smtp.get("SMTP_SECURE", "").lower() in ("1", "true", "yes"),
    }


def send_failure_alert(failed_reports: list, run_tier: str, reports_dir: str) -> None:
    """Send one email summarising all failures from a run."""
    cfg = _load_config()

    n = len(failed_reports)
    today = __import__("datetime").date.today().isoformat()
    subject = f"Bosly Gov: {n} check{'s' if n != 1 else ''} failed — {today}"

    lines = [
        f"Bosly Gov {run_tier} tier run — {today}",
        "",
        f"{n} check{'s' if n != 1 else ''} failed:",
        "",
    ]
    for r in failed_reports:
        lines.append(f"  [FAIL] {r['check_id']}")
        lines.append(f"    project:  {r['project']}")
        lines.append(f"    severity: {r['severity']}")
        lines.append(f"    duration: {r['duration_ms']}ms")
        if r.get("report_path"):
            lines.append(f"    report:   {r['report_path']}")
        lines.append("")

    lines.append("Report directory: " + reports_dir)
    lines.append("")
    lines.append("— Bosly Gov")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from"]
    msg["To"] = cfg["to"]
    msg.set_content("\n".join(lines))

    if cfg["secure"]:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx) as s:
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)


if __name__ == "__main__":
    # Self-test: read config and print what it would do, without sending.
    cfg = _load_config()
    print("SMTP host: " + cfg["host"])
    print("SMTP port: " + str(cfg["port"]))
    print("SMTP user set: " + str(bool(cfg["user"])))
    print("SMTP password set: " + str(bool(cfg["password"])))
    print("From set: " + str(bool(cfg["from"])))
    print("Recipient set: " + str(bool(cfg["to"])))
    print("Secure (SSL): " + str(cfg["secure"]))
