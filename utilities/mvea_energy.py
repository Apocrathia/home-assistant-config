#!/usr/bin/env python3
"""Fetch MVEA energy usage from SmartHub and print JSON for HA command_line sensor."""
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit('pip install requests')

BASE_URL = "https://mvea.smarthub.coop/services"
TOKEN_CACHE = Path("/tmp/mvea_token.json")


def get_token(user: str, password: str) -> str:
    # Return cached token if still valid (with 5 min buffer)
    if TOKEN_CACHE.exists():
        cached = json.loads(TOKEN_CACHE.read_text())
        if cached.get("expiration", 0) - time.time() > 300:
            return cached["token"]

    resp = requests.get(
        f"{BASE_URL}/auth/login",
        params={"userId": user, "password": password, "AUTH_SOURCE": "CIS"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["authorizationToken"]
    # expiration is epoch ms in the response
    expiration = data.get("expiration", 0) / 1000
    TOKEN_CACHE.write_text(json.dumps({"token": token, "expiration": expiration}))
    return token


def fetch_usage(
    token: str,
    account: str,
    service_location: str,
    days: int = 30,
    time_frame: str = "Daily",
) -> list[dict]:
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 60 * 60 * 1000
    resp = requests.get(
        f"{BASE_URL}/secured/greenButtonCsvDownload",
        params={
            "account": account,
            "serviceLocation": service_location,
            "timeFrame": time_frame,
            "startDate": start_ms,
            "endDate": end_ms,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    readings = []
    for line in resp.text.splitlines():
        # Data lines look like: "2026-05-16 00:00 to 2026-06-16 00:00,43.000,,"
        if " to " in line and "," in line and not line.startswith(" "):
            parts = line.split(",")
            period, kwh_str = parts[0].strip(), parts[1].strip()
            try:
                start_str = period.split(" to ")[0].strip()
                readings.append({"date": start_str, "kwh": float(kwh_str)})
            except (ValueError, IndexError):
                continue
    return readings


def main():
    user = os.environ.get("MVEA_USER")
    password = os.environ.get("MVEA_PASS")
    account = os.environ.get("MVEA_ACCOUNT")
    service_location = os.environ.get("MVEA_SERVICE_LOCATION")
    missing = [
        name
        for name, value in (
            ("MVEA_USER", user),
            ("MVEA_PASS", password),
            ("MVEA_ACCOUNT", account),
            ("MVEA_SERVICE_LOCATION", service_location),
        )
        if not value
    ]
    if missing:
        sys.exit(f"Set environment variables: {', '.join(missing)}")

    try:
        token = get_token(user, password)
        readings = fetch_usage(token, account, service_location)
    except requests.HTTPError:
        # Token may be stale — clear cache and retry once
        TOKEN_CACHE.unlink(missing_ok=True)
        token = get_token(user, password)
        readings = fetch_usage(token, account, service_location)

    if not readings:
        print(json.dumps({"error": "no data"}))
        return

    latest = readings[-1]
    print(json.dumps({
        "kwh": latest["kwh"],
        "date": latest["date"],
        "readings": readings[-7:],  # last 7 days for attributes
    }))


if __name__ == "__main__":
    main()
