"""Minimal black-box check for a running local Docker environment."""

import json
import os
from urllib.request import Request, urlopen


BASE_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
PASSWORD = os.getenv("DEV_SEED_PASSWORD", "")


def request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=10)
    return json.loads(response.read().decode("utf-8"))


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the smoke test.")
    health = request("/health")
    assert health["status"] == "ok"
    login = request("/auth/login", method="POST", payload={"username": "dev-admin", "password": PASSWORD})
    profile = request("/auth/me", token=login["access_token"])
    assert profile["username"] == "dev-admin"
    assert "ADMIN" in profile["roles"]
    print("Local API smoke test passed.")


if __name__ == "__main__":
    main()
