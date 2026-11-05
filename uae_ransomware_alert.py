#!/usr/bin/env python3
"""
Ransomware Country Alerts with respect to UAE.
Polls ransomware.live for new victims in a country and emails an alert for
each one not already recorded in seen_victims.json. The workflow commits that
file back after each run, so state persists without a server.
"""

import base64
import html
import json
import os
import re
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

COUNTRY = (os.environ.get("COUNTRY") or "AE").strip().upper()
API_URL = f"https://api.ransomware.live/v2/countryvictims/{COUNTRY}"
STATE_FILE = Path("seen_victims.json")

SMTP_HOST = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "465")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
ALERT_TO = os.environ.get("ALERT_TO") or SMTP_USER


def victim_key(v: dict) -> str:
    return (
        f"{v.get('group_name','')}|{v.get('website','')}|{v.get('post_title','')}"
        f"|{v.get('published','')}|{v.get('discovered','')}"
    )


def load_seen() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set):
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=2))


def fetch_victims() -> list:
    resp = requests.get(API_URL, timeout=20)
    if resp.status_code == 429:
        print("Rate limited by ransomware.live (429). Will retry on the next run.")
        sys.exit(0)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        data = data.get("victims", data.get("data", []))
    return data or []


def get_victim_page_url(name: str, group: str) -> str:
    raw = f"{name}@{group}"
    vid = base64.b64encode(raw.encode()).decode().rstrip("=")
    return f"https://www.ransomware.live/id/{vid}"


def get_screenshot_url(v: dict):
    group = v.get("group_name", "")
    tried = set()
    for name in [v.get("post_title", ""), v.get("website", "")]:
        if not name or name in tried:
            continue
        tried.add(name)
        page_url = get_victim_page_url(name, group)
        try:
            resp = requests.get(page_url, timeout=15)
            if resp.status_code == 200:
                m = re.search(r'property="og:image" content="([^"]+)"', resp.text)
                if m:
                    return m.group(1)
        except requests.RequestException as e:
            print(f"Screenshot lookup failed for {page_url}: {e}")
    return None


def send_email(subject: str, text_body: str, html_body: str):
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP_USER / SMTP_PASS secrets are not set")

    recipients = [a.strip() for a in ALERT_TO.split(",") if a.strip()]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg, to_addrs=recipients)
    print(f"Email sent: {subject}")


def main():
    first_run = not STATE_FILE.exists()
    seen = load_seen()

    try:
        victims = fetch_victims()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        sys.exit(1)

    if first_run:
        print(f"First run: baselining {len(victims)} existing victims without emailing.")
        save_seen({victim_key(v) for v in victims})
        return

    new_victims = [v for v in victims if victim_key(v) not in seen]

    for v in new_victims:
        key = victim_key(v)
        victim_name = v.get("post_title") or v.get("website") or "Unknown"
        website = v.get("website") or "Unknown"
        group = v.get("group_name") or "Unknown group"
        published = v.get("published") or "Unknown"
        discovered = v.get("discovered") or "Unknown"
        country = v.get("country") or COUNTRY
        sector = v.get("activity") or "Unknown"
        post_url = v.get("post_url") or "N/A"
        description = v.get("description") or "N/A"
        screenshot_url = get_screenshot_url(v)

        subject = f"⚠️ New {COUNTRY} ransomware claim: {group}"

        text_body = (
            f"Victim: {victim_name}\nWebsite: {website}\nGroup: {group}\n"
            f"Published: {published}\nDiscovered by ransomware.live: {discovered}\n"
            f"Country: {country}\nSector: {sector}\nLeak post: {post_url}\n"
            f"\nDescription:\n{description}\n"
        )
        if screenshot_url:
            text_body += f"\nLeak screenshot: {screenshot_url}\n"

        screenshot_html = (
            f'<p><img src="{html.escape(screenshot_url)}" alt="Leak site screenshot" '
            f'style="max-width:600px;border:1px solid #ccc;"></p>'
            if screenshot_url
            else "<p><em>No screenshot available for this claim.</em></p>"
        )

        html_body = f"""\
<html>
<body style="font-family: sans-serif; line-height: 1.5;">
  <h2 style="color:#b00020;">⚠️ New {html.escape(COUNTRY)} ransomware claim: {html.escape(group)}</h2>
  <table cellpadding="4">
    <tr><td><b>Victim</b></td><td>{html.escape(victim_name)}</td></tr>
    <tr><td><b>Website</b></td><td>{html.escape(website)}</td></tr>
    <tr><td><b>Group</b></td><td>{html.escape(group)}</td></tr>
    <tr><td><b>Published</b></td><td>{html.escape(published)}</td></tr>
    <tr><td><b>Discovered</b></td><td>{html.escape(discovered)}</td></tr>
    <tr><td><b>Country</b></td><td>{html.escape(country)}</td></tr>
    <tr><td><b>Sector</b></td><td>{html.escape(sector)}</td></tr>
    <tr><td><b>Leak post</b></td><td>{html.escape(post_url)}</td></tr>
  </table>
  <p><b>Description:</b><br>{html.escape(description).replace(chr(10), '<br>')}</p>
  {screenshot_html}
</body>
</html>
"""
        try:
            send_email(subject, text_body, html_body)
            seen.add(key)  # only mark as seen after a successful send
        except Exception as e:
            print(f"Failed to send email for {key}: {e} (will retry next run)")

    save_seen(seen)
    print(f"Run complete. {len(new_victims)} new victim(s) out of {len(victims)} checked.")


if __name__ == "__main__":
    main()
