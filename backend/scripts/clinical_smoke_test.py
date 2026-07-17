"""Black-box clinical MVP and specimen traceability checks."""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


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


def expect_status(expected_status: int, path: str, method: str, payload: dict, token: str) -> None:
    try:
        request(path, method=method, payload=payload, token=token)
    except HTTPError as error:
        assert error.code == expected_status, error.read().decode("utf-8")
    else:
        raise AssertionError(f"Expected HTTP {expected_status} for {method} {path}.")


def login(username: str) -> str:
    return request("/auth/login", method="POST", payload={"username": username, "password": PASSWORD})["access_token"]


def catalog_item(path: str, code: str, token: str) -> dict:
    page = request(f"/catalogs/{path}?search={code}", token=token)
    return next(item for item in page["data"] if item["code"] == code)


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the clinical smoke test.")

    admin_token = login("dev-admin")
    entry_token = login("dev-entry")
    processor_token = login("dev-processor")

    assert request("/patients?search=DEV-HC-0001", token=entry_token)["total"] == 1
    assert request("/orders?search=DEV-ORDER-0001", token=entry_token)["total"] == 1

    origin = catalog_item("origins", "HOSPITALIZACION", entry_token)
    service = catalog_item("services", "EMERGENCIA", entry_token)
    clinician = catalog_item("clinicians", "DEV-CLINICIAN", entry_token)
    destination = catalog_item("destinations", "MICROBIOLOGY_BENCH", entry_token)
    exam = catalog_item("exams", "URINE_CULTURE", entry_token)
    specimen_type = catalog_item("specimen-types", "URO_CHORRO_MEDIO", entry_token)

    suffix = uuid4().hex[:8].upper()
    medical_record_number = f"PRUEBA-HC-{suffix}"
    document_number = f"PRB-{suffix}"
    patient_payload = {
        "medical_record_number": medical_record_number.lower(),
        "document_number": document_number.lower(),
        "family_name": "FICTICIO",
        "given_name": f"PRUEBA {suffix}",
        "birth_date": "1995-05-20",
        "sex": "X",
    }
    patient = request("/patients", method="POST", payload=patient_payload, token=entry_token)
    assert patient["medical_record_number"] == medical_record_number
    assert request(f"/patients?search={medical_record_number}", token=processor_token)["total"] == 1
    patient = request(
        f"/patients/{patient['id']}",
        method="PATCH",
        payload={"given_name": f"ACTUALIZADO {suffix}"},
        token=entry_token,
    )
    assert patient["given_name"] == f"ACTUALIZADO {suffix}"
    expect_status(409, "/patients", "POST", patient_payload, entry_token)

    now = datetime.now(timezone.utc)
    order = request(
        "/orders",
        method="POST",
        payload={
            "patient_id": patient["id"],
            "ordered_at": (now - timedelta(minutes=30)).isoformat(),
            "origin_id": origin["id"],
            "service_id": service["id"],
            "clinician_id": clinician["id"],
            "clinical_notes": "ORDEN DE PRUEBA ESTRICTAMENTE FICTICIA.",
        },
        token=entry_token,
    )
    assert re.fullmatch(r"\d{8}-\d{6}", order["order_number"])
    order = request(
        f"/orders/{order['id']}",
        method="PATCH",
        payload={"clinical_notes": "ORDEN FICTICIA DE PRUEBA ACTUALIZADA."},
        token=entry_token,
    )
    assert order["clinical_notes"].startswith("ORDEN")

    first_item = request(
        f"/orders/{order['id']}/items",
        method="POST",
        payload={"exam_id": exam["id"], "specimen_type_id": specimen_type["id"]},
        token=entry_token,
    )
    assert first_item["status"] == "REGISTERED"
    collected_at = now - timedelta(minutes=20)
    first_item = request(
        f"/order-items/{first_item['id']}/collect",
        method="POST",
        payload={"collection_at": collected_at.isoformat(), "location": "SALA FICTICIA DE RECOLECCION"},
        token=entry_token,
    )
    assert first_item["status"] == "COLLECTED"
    first_item = request(
        f"/order-items/{first_item['id']}/receive",
        method="POST",
        payload={
            "received_at": (now - timedelta(minutes=10)).isoformat(),
            "destination_id": destination["id"],
            "location": "MESA FICTICIA DE MICROBIOLOGIA",
        },
        token=processor_token,
    )
    assert first_item["status"] == "RECEIVED"

    second_item = request(
        f"/orders/{order['id']}/items",
        method="POST",
        payload={"exam_id": exam["id"], "specimen_type_id": specimen_type["id"]},
        token=entry_token,
    )
    assert second_item["barcode"] != first_item["barcode"]
    second_item = request(
        f"/order-items/{second_item['id']}/reject",
        method="POST",
        payload={"reason": "MUESTRA FICTICIA INSUFICIENTE."},
        token=processor_token,
    )
    assert second_item["status"] == "REJECTED"
    second_item = request(
        f"/order-items/{second_item['id']}/reopen",
        method="POST",
        payload={"reason": "CORRECCION FICTICIA APROBADA."},
        token=admin_token,
    )
    assert second_item["status"] == "REGISTERED"
    second_item = request(
        f"/order-items/{second_item['id']}/cancel",
        method="POST",
        payload={"reason": "CORRECCION FICTICIA DE LA ORDEN."},
        token=entry_token,
    )
    assert second_item["status"] == "CANCELLED"
    request(
        f"/order-items/{second_item['id']}/reopen",
        method="POST",
        payload={"reason": "ELEMENTO FICTICIO RESTAURADO."},
        token=admin_token,
    )

    third_item = request(
        f"/orders/{order['id']}/items",
        method="POST",
        payload={"exam_id": exam["id"], "specimen_type_id": specimen_type["id"]},
        token=entry_token,
    )
    expect_status(
        422,
        f"/order-items/{third_item['id']}/receive",
        "POST",
        {"received_at": now.isoformat(), "destination_id": destination["id"]},
        processor_token,
    )
    expect_status(
        403,
        f"/order-items/{third_item['id']}/reject",
        "POST",
        {"reason": "EL USUARIO DE REGISTRO NO DEBE RECHAZAR MUESTRAS."},
        entry_token,
    )

    cancelled_order = request(
        f"/orders/{order['id']}/cancel",
        method="POST",
        payload={"reason": "PRUEBA FICTICIA DE ANULACION DE ORDEN."},
        token=entry_token,
    )
    assert cancelled_order["status"] == "CANCELLED"
    reopened_order = request(
        f"/orders/{order['id']}/reopen",
        method="POST",
        payload={"reason": "PRUEBA FICTICIA DE REAPERTURA DE ORDEN."},
        token=admin_token,
    )
    assert reopened_order["status"] == "REGISTERED"
    restored = {item["id"]: item["status"] for item in reopened_order["items"]}
    assert restored[first_item["id"]] == "RECEIVED"
    assert restored[third_item["id"]] == "REGISTERED"

    events = request(f"/order-items/{first_item['id']}/events", token=processor_token)
    event_types = [event["event_type"] for event in events]
    assert {"REGISTERED", "COLLECTED", "RECEIVED", "CANCELLED", "REOPENED"}.issubset(event_types)
    assert request(f"/orders?search={order['order_number']}", token=processor_token)["total"] == 1
    print("Clinical workflow smoke test passed.")


if __name__ == "__main__":
    main()
