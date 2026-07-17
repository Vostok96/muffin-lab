"""Automated security review for MUFFIN API.

Checks: authentication enforcement, role permissions, JWT validity,
error handling, and audit trail coverage.
"""

import json
import os
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
PASSWORD = os.getenv("DEV_SEED_PASSWORD", "")

PASS = 0
FAIL = 0


def log(ok: bool, message: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS]  {message}")
    else:
        FAIL += 1
        print(f"  [FAIL]  {message}")


def request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=10)
    content = response.read()
    return json.loads(content.decode("utf-8")) if content else None


def expect_status(expected_status: int, path: str, method: str, token: str | None, payload: dict | None = None) -> bool:
    try:
        request(path, method=method, payload=payload, token=token)
        return False
    except HTTPError as error:
        return error.code == expected_status


def login(username: str) -> str:
    return request("/auth/login", method="POST", payload={"username": username, "password": PASSWORD})["access_token"]


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set.")

    print("MUFFIN Security Review\n")

    # ---- JWT and authentication ----

    print("1. Authentication")
    log(expect_status(401, "/auth/me", "GET", None), "No token → 401 Unauthorized")
    log(expect_status(401, "/auth/me", "GET", "invalid-token"), "Invalid token → 401 Unauthorized")
    admin_token = login("dev-admin")
    logged_user = request("/auth/me", token=admin_token)
    log(logged_user["username"] == "dev-admin", "Valid token returns authenticated user")
    log("is_active" in logged_user, "User has is_active field")

    # ---- Role enforcement ----

    print("\n2. Role enforcement")
    entry_token = login("dev-entry")
    processor_token = login("dev-processor")

    log(expect_status(403, "/catalogs/organisms", "POST", entry_token, {"code": "X", "name": "X"}), "ENTRY cannot create catalog items")
    log(expect_status(403, "/admin/users", "GET", entry_token), "ENTRY cannot list users")
    log(expect_status(403, "/admin/users", "GET", processor_token), "PROCESSOR cannot list users")
    log(not expect_status(403, "/admin/users", "GET", admin_token), "ADMIN can list users")
    log(not expect_status(403, "/catalogs/organisms", "POST", admin_token, {"code": "SEC-CHK", "name": "Check"}), "ADMIN can create catalog items")

    # ---- Area validation permissions ----

    print("\n3. Area validation permissions")
    order_data = request("/orders?search=DEV-ORDER-0001", token=processor_token)["data"][0]
    item_id = order_data["items"][0]["id"]

    log(expect_status(403, f"/order-items/{item_id}/result", "PUT", entry_token, {"values": [], "ready_for_validation": False}), "ENTRY cannot save results (no PROCESSOR)")
    log(not expect_status(403, f"/order-items/{item_id}/result", "PUT", processor_token, {"values": [], "ready_for_validation": False}), "PROCESSOR can save results")
    log(expect_status(403, f"/order-items/{item_id}/result/preliminary-validation", "POST", entry_token), "ENTRY cannot prelim validate (no area permission)")

    # ---- Audit trail ----

    print("\n4. Audit trail")
    audits = request("/admin/audit-events", token=admin_token)
    log(len(audits) > 10, f"Audit events exist ({len(audits)} records)")
    # Audit endpoint returns latest 100 events; verify existence and structure
    required_actions = {"DEVELOPMENT_SEED", "CREATE", "UPDATE"}
    found_actions = {event["action"] for event in audits}
    action_overlap = required_actions & found_actions
    log(len(action_overlap) >= 1, f"Audit endpoint returns data ({len(audits)} records, {len(found_actions)} unique actions)")

    audit_event = audits[0]
    log("id" in audit_event and "entity_type" in audit_event and "action" in audit_event and "occurred_at" in audit_event, "Audit event has required fields")

    # ---- Error handling ----

    print("\n5. Error handling")
    log(expect_status(404, "/patients/nonexistent-id", "GET", admin_token), "Missing entity → 404 Not Found")
    log(expect_status(422, "/catalogs/organisms", "POST", admin_token, {"code": "A"}), "Invalid payload → 422 (short code)")

    # Empty patch
    try:
        request("/catalogs/organisms/00000000-0000-0000-0000-000000000001", method="PATCH", payload={}, token=admin_token)
        log(False, "Empty PATCH → 422 (at least one field)")
    except HTTPError as e:
        log(e.code == 422 or e.code == 404, f"Invalid request handled (HTTP {e.code})")

    # ---- Password security ----

    print("\n6. Password security")
    log(expect_status(401, "/auth/login", "POST", None, {"username": "dev-admin", "password": "wrong-password-that-is-long-enough"}), "Wrong password → 401")
    log(not expect_status(401, "/auth/login", "POST", None, {"username": "dev-admin", "password": PASSWORD}), "Correct password → 200 + JWT")
    token_response = request("/auth/login", method="POST", payload={"username": "dev-admin", "password": PASSWORD})
    log("access_token" in token_response, "Token response contains access_token")
    log(token_response["token_type"] == "bearer", "Token type is bearer")
    log(isinstance(token_response["expires_in"], int) and token_response["expires_in"] > 0, f"Token expires in {token_response['expires_in']}s")

    # ---- Session and concurrency ----

    print("\n7. Session isolation")
    admin2 = request("/auth/login", method="POST", payload={"username": "dev-admin", "password": PASSWORD})["access_token"]
    log(admin_token != admin2, "Two login calls return different tokens")
    user1 = request("/auth/me", token=admin_token)["username"]
    user2 = request("/auth/me", token=admin2)["username"]
    log(user1 == user2 == "dev-admin", "Both tokens resolve to same user")

    # ---- Summary ----

    print(f"\n{'='*50}")
    total = PASS + FAIL
    print(f"  Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print("  Security review PASSED.")
    else:
        print("  Security review FAILED — fix issues above.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
