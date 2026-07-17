"""Black-box dynamic result and validation workflow checks."""

import json
import os
from datetime import datetime, timedelta, timezone
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


def catalog_item(path: str, code: str, token: str) -> dict:
    page = request(f"/catalogs/{path}?search={code}", token=token)
    return next(item for item in page["data"] if item["code"] == code)


def result_value(form: dict, code: str) -> dict:
    return next(value for value in form["values"] if value["code"] == code)


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the result smoke test.")

    admin_token = login("dev-admin")
    entry_token = login("dev-entry")
    processor_token = login("dev-processor")

    seeded_order = request("/orders?search=DEV-ORDER-0001", token=processor_token)["data"][0]
    seeded_result = request(f"/order-items/{seeded_order['items'][0]['id']}/result", token=processor_token)
    assert seeded_result["status"] == "RESULT_SAVED"
    assert result_value(seeded_result, "CULTURE_RESULT")["value_code"] == "NEGATIVO"

    patient = request("/patients?search=DEV-HC-0001", token=processor_token)["data"][0]
    origin = catalog_item("origins", "HOSPITALIZACION", processor_token)
    service = catalog_item("services", "EMERGENCIA", processor_token)
    clinician = catalog_item("clinicians", "DEV-CLINICIAN", processor_token)
    destination = catalog_item("destinations", "MICROBIOLOGY_BENCH", processor_token)
    exam = catalog_item("exams", "URINE_CULTURE", processor_token)
    specimen_type = catalog_item("specimen-types", "URO_CHORRO_MEDIO", processor_token)

    now = datetime.now(timezone.utc)
    order = request(
        "/orders",
        method="POST",
        payload={
            "patient_id": patient["id"],
            "ordered_at": (now - timedelta(minutes=40)).isoformat(),
            "origin_id": origin["id"],
            "service_id": service["id"],
            "clinician_id": clinician["id"],
            "clinical_notes": "ORDEN FICTICIA PARA PRUEBA DE RESULTADOS.",
        },
        token=entry_token,
    )
    item = request(
        f"/orders/{order['id']}/items",
        method="POST",
        payload={"exam_id": exam["id"], "specimen_type_id": specimen_type["id"]},
        token=entry_token,
    )
    item = request(
        f"/order-items/{item['id']}/receive",
        method="POST",
        payload={
            "collection_at": (now - timedelta(minutes=30)).isoformat(),
            "received_at": (now - timedelta(minutes=20)).isoformat(),
            "destination_id": destination["id"],
            "location": "MESA FICTICIA PARA PRUEBA DE RESULTADOS",
        },
        token=processor_token,
    )
    assert item["status"] == "RECEIVED"

    result_path = f"/order-items/{item['id']}/result"
    form = request(result_path, token=processor_token)
    assert form["id"] is None
    assert form["status"] == "NOT_STARTED"
    assert {value["code"] for value in form["values"]} >= {
        "CULTURE_RESULT",
        "CULTURE_OBSERVATION",
        "CULTURE_GRAM",
        "CULTURE_NITRITE",
        "CULTURE_COLONY_COUNT",
        "CULTURE_ANTIMICROBIAL_ACTIVITY",
    }
    parameter = result_value(form, "CULTURE_RESULT")
    assert parameter["is_required"] is True
    parameter_id = parameter["parameter_definition_id"]

    expect_status(403, result_path, "PUT", entry_token, {"values": []})
    expect_status(
        422,
        result_path,
        "PUT",
        processor_token,
        {
            "ready_for_validation": False,
            "values": [{"parameter_definition_id": parameter_id, "value_code": "NO_CONFIGURADO"}],
        },
    )

    draft = request(
        result_path,
        method="PUT",
        payload={"ready_for_validation": False, "values": []},
        token=processor_token,
    )
    assert draft["status"] == "IN_PROCESS"
    assert draft["id"] is not None
    expect_status(409, f"{result_path}/preliminary-validation", "POST", processor_token)
    expect_status(
        422,
        result_path,
        "PUT",
        processor_token,
        {"ready_for_validation": True, "values": []},
    )

    ready_payload = {
        "ready_for_validation": True,
        "values": [
            {
                "parameter_definition_id": parameter_id,
                "value_code": "NEGATIVO",
                "observed_at": (now - timedelta(minutes=5)).isoformat(),
            }
        ],
    }
    saved = request(result_path, method="PUT", payload=ready_payload, token=processor_token)
    assert saved["status"] == "RESULT_SAVED"
    assert result_value(saved, "CULTURE_RESULT")["value_code"] == "NEGATIVO"
    assert result_value(saved, "CULTURE_RESULT")["value_text"] == "NEGATIVO"

    expect_status(403, f"{result_path}/preliminary-validation", "POST", entry_token)
    preliminary = request(f"{result_path}/preliminary-validation", method="POST", token=processor_token)
    assert preliminary["status"] == "PRELIMINARY_VALIDATED"
    assert preliminary["preliminary_by"] is not None

    edited_payload = {
        "ready_for_validation": True,
        "values": [{"parameter_definition_id": parameter_id, "value_code": "POSITIVO"}],
    }
    edited = request(result_path, method="PUT", payload=edited_payload, token=processor_token)
    assert edited["status"] == "RESULT_SAVED"
    assert edited["preliminary_at"] is None
    assert result_value(edited, "CULTURE_RESULT")["value_code"] == "POSITIVO"
    expect_status(409, f"{result_path}/final-validation", "POST", processor_token)

    request(f"{result_path}/preliminary-validation", method="POST", token=processor_token)
    final = request(f"{result_path}/final-validation", method="POST", token=processor_token)
    assert final["status"] == "FINAL_VALIDATED"
    assert final["final_by"] is not None
    expect_status(409, result_path, "PUT", processor_token, edited_payload)
    expect_status(
        403,
        f"{result_path}/reopen",
        "POST",
        entry_token,
        {"reason": "EL USUARIO DE REGISTRO NO PUEDE REABRIR UN RESULTADO FINAL."},
    )

    reopened = request(
        f"{result_path}/reopen",
        method="POST",
        payload={"reason": "CORRECCION FICTICIA DEL RESULTADO FINAL."},
        token=processor_token,
    )
    assert reopened["status"] == "RESULT_SAVED"
    assert reopened["preliminary_at"] is None
    assert reopened["final_at"] is None
    request(f"{result_path}/preliminary-validation", method="POST", token=processor_token)
    final = request(f"{result_path}/final-validation", method="POST", token=processor_token)
    assert final["status"] == "FINAL_VALIDATED"

    order_detail = request(f"/orders/{order['id']}", token=processor_token)
    assert order_detail["items"][0]["status"] == "FINAL_VALIDATED"
    events = request(f"/order-items/{item['id']}/events", token=processor_token)
    event_types = {event["event_type"] for event in events}
    assert {
        "RESULT_IN_PROCESS",
        "RESULT_SAVED",
        "PRELIMINARY_VALIDATED",
        "PRELIMINARY_INVALIDATED",
        "FINAL_VALIDATED",
        "RESULT_REOPENED",
    }.issubset(event_types)

    audits = request("/admin/audit-events", token=admin_token)
    result_actions = {event["action"] for event in audits if event["entity_id"] == final["id"]}
    assert {"SAVE", "PRELIMINARY_VALIDATE", "FINAL_VALIDATE", "REOPEN"}.issubset(result_actions)
    print("Result validation smoke test passed.")


if __name__ == "__main__":
    main()
