"""Black-box outputs and integrations workflow checks."""

import json
import os
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
PASSWORD = os.getenv("DEV_SEED_PASSWORD", "")


def request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=10)
    content = response.read()
    return json.loads(content.decode("utf-8")) if content else None


def expect_status(
    expected_status: int,
    path: str,
    method: str,
    token: str,
    payload: dict | None = None,
) -> None:
    try:
        request(path, method=method, payload=payload, token=token)
    except HTTPError as error:
        assert error.code == expected_status, error.read().decode("utf-8")
    else:
        raise AssertionError(f"Expected HTTP {expected_status} for {method} {path}.")


def login(username: str) -> str:
    return request("/auth/login", method="POST", payload={"username": username, "password": PASSWORD})["access_token"]


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the outputs smoke test.")

    admin_token = login("dev-admin")
    entry_token = login("dev-entry")
    processor_token = login("dev-processor")

    seeded_order = request("/orders?search=DEV-ORDER-0001", token=processor_token)["data"][0]
    item = seeded_order["items"][0]

    # --- Print jobs ---

    print_jobs = request("/print-jobs", token=processor_token)["data"]
    assert len(print_jobs) >= 1
    seeded_print = next((p for p in print_jobs if p["kind"] == "LABEL"), None)
    assert seeded_print is not None
    assert seeded_print["status"] == "PRINTED"

    new_job = request(
        "/print-jobs",
        method="POST",
        payload={"order_item_id": item["id"], "kind": "REPORT", "details": "SOLICITUD DE INFORME DE PRUEBA"},
        token=entry_token,
    )
    assert new_job["status"] == "PENDING"
    assert new_job["kind"] == "REPORT"

    completed = request(f"/print-jobs/{new_job['id']}/complete", method="PATCH", token=processor_token)
    assert completed["status"] == "PRINTED"
    assert completed["printed_at"] is not None

    job2 = request(
        "/print-jobs",
        method="POST",
        payload={"order_item_id": item["id"], "kind": "BARCODE"},
        token=processor_token,
    )
    failed = request(f"/print-jobs/{job2['id']}/fail", method="PATCH", token=processor_token)
    assert failed["status"] == "FAILED"

    expect_status(409, f"/print-jobs/{new_job['id']}/complete", "PATCH", processor_token)

    # --- Notifications ---

    notifications = request("/notifications", token=processor_token)["data"]
    assert len(notifications) >= 2
    sent_notif = next((n for n in notifications if n["status"] == "SENT"), None)
    assert sent_notif is not None
    failed_notif = next((n for n in notifications if n["status"] == "FAILED"), None)
    assert failed_notif is not None

    new_notif = request(
        "/notifications",
        method="POST",
        payload={
            "order_item_id": item["id"],
            "type": "CRITICAL_VALUE",
            "recipient": "dev@example.invalid",
            "payload": {"value": "ORGANISMO PANRESISTENTE DETECTADO"},
        },
        token=processor_token,
    )
    assert new_notif["status"] == "PENDING"

    updated = request(
        f"/notifications/{new_notif['id']}",
        method="PATCH",
        payload={"status": "SENT"},
        token=processor_token,
    )
    assert updated["status"] == "SENT"
    assert updated["sent_at"] is not None

    retry_target = request(
        f"/notifications/{failed_notif['id']}/retry",
        method="POST",
        token=processor_token,
    )
    assert retry_target["status"] == "PENDING"
    assert retry_target["error_message"] is None
    expect_status(409, f"/notifications/{updated['id']}/retry", "POST", processor_token)

    # --- Instrument messages ---

    ims = request("/instrument-messages", token=processor_token)["data"]
    assert len(ims) >= 2
    outbound = next((m for m in ims if m["direction"] == "OUTBOUND"), None)
    assert outbound is not None
    inbound = next((m for m in ims if m["direction"] == "INBOUND"), None)
    assert inbound is not None

    new_im = request(
        "/instrument-messages",
        method="POST",
        payload={
            "order_item_id": item["id"],
            "direction": "OUTBOUND",
            "payload": {"instrument": "MALDI-TOF", "action": "IDENTIFICAR"},
        },
        token=processor_token,
    )
    assert new_im["status"] == "PENDING"

    processed = request(
        f"/instrument-messages/{new_im['id']}",
        method="PATCH",
        payload={"status": "PROCESSED", "result_summary": "IDENTIFICACION MALDI-TOF COMPLETADA."},
        token=processor_token,
    )
    assert processed["status"] == "PROCESSED"
    assert processed["processed_at"] is not None

    item_ims = request(f"/order-items/{item['id']}/instrument-messages", token=processor_token)
    assert len(item_ims) >= 3

    print("Outputs and integrations smoke test passed.")


if __name__ == "__main__":
    main()
