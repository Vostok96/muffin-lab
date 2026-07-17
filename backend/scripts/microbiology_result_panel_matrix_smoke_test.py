"""Matrix smoke test for microbiology culture states and AST panel registration."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
ORGANISM_LIMIT = int(os.getenv("MATRIX_ORGANISM_LIMIT", "8"))


def request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=20)
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


def login(username: str, password: str) -> str:
    return request("/auth/login", method="POST", payload={"username": username, "password": password})["access_token"]


def catalog_item(path: str, code: str, token: str) -> dict:
    page = request(f"{path}?search={quote(code, safe='')}&page_size=100", token=token)
    return next(item for item in page["data"] if item["code"] == code)


def result_value(form: dict, code: str) -> dict:
    return next(value for value in form["values"] if value["code"] == code)


def active_catalog_items(path: str, token: str, limit: int | None = None) -> list[dict]:
    page = request(f"{path}?active_only=true&page_size=100", token=token)
    items = list(page["data"])
    return items if limit is None else items[:limit]


def main() -> None:
    admin_token = login("admin", "admin")

    patient = request("/patients?search=DEV-HC-0001&page_size=100", token=admin_token)["data"][0]
    origin = catalog_item("/catalogs/origins", "HOSPITALIZACION", admin_token)
    service = catalog_item("/catalogs/services", "EMERGENCIA", admin_token)
    clinician = catalog_item("/catalogs/clinicians", "DEV-CLINICIAN", admin_token)
    destination = catalog_item("/catalogs/destinations", "MICROBIOLOGY_BENCH", admin_token)
    exam = catalog_item("/catalogs/exams", "URINE_CULTURE", admin_token)
    specimen_type = catalog_item("/catalogs/specimen-types", "URO_CHORRO_MEDIO", admin_token)

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
            "clinical_notes": "ORDEN FICTICIA PARA MATRIZ DE CULTIVO Y PANEL.",
        },
        token=admin_token,
    )
    item = request(
        f"/orders/{order['id']}/items",
        method="POST",
        payload={"exam_id": exam["id"], "specimen_type_id": specimen_type["id"]},
        token=admin_token,
    )
    item = request(
        f"/order-items/{item['id']}/receive",
        method="POST",
        payload={
            "collection_at": (now - timedelta(minutes=30)).isoformat(),
            "received_at": (now - timedelta(minutes=20)).isoformat(),
            "destination_id": destination["id"],
            "location": "MESA FICTICIA PARA MATRIZ",
        },
        token=admin_token,
    )
    assert item["status"] == "RECEIVED"

    result_path = f"/order-items/{item['id']}/result"
    form = request(result_path, token=admin_token)
    result_param = result_value(form, "CULTURE_RESULT")
    result_param_id = result_param["parameter_definition_id"]

    panel_items = active_catalog_items("/catalogs/ast-panels", admin_token)
    organism_items = active_catalog_items("/catalogs/organisms", admin_token, ORGANISM_LIMIT)
    assert panel_items, "No active AST panels found."
    assert organism_items, "No active organisms found."

    for code in ["NEGATIVO", "POSITIVO", "NO_TRAJO_MUESTRA", "MUESTRA_INADECUADA"]:
        saved = request(
            result_path,
            method="PUT",
            payload={
                "ready_for_validation": False,
                "values": [
                    {
                        "parameter_definition_id": result_param_id,
                        "value_code": code,
                        "observed_at": (now - timedelta(minutes=5)).isoformat(),
                    }
                ],
            },
            token=admin_token,
        )
        assert result_value(saved, "CULTURE_RESULT")["value_code"] == code
        refreshed = request(result_path, token=admin_token)
        assert result_value(refreshed, "CULTURE_RESULT")["value_code"] == code

        if code != "POSITIVO":
            continue

        for panel in panel_items:
            panel_antibiotics = request(f"/catalogs/ast-panels/{panel['id']}/antibiotics", token=admin_token)
            for organism in organism_items:
                isolate = request(
                    f"/results/{saved['id']}/isolates",
                    method="POST",
                    payload={
                        "organism_id": organism["id"],
                        "ast_panel_id": panel["id"],
                    },
                    token=admin_token,
                )
                ars = request(f"/isolates/{isolate['id']}/antimicrobial-results", token=admin_token)
                assert len(ars) == len(panel_antibiotics)
                request(f"/results/{saved['id']}/isolates/{isolate['id']}", method="DELETE", token=admin_token)

    final_isolates = request(f"/results/{saved['id']}/isolates", token=admin_token)
    assert final_isolates == [], "The matrix test left behind isolates."
    print("Microbiology result/panel matrix smoke test passed.")


if __name__ == "__main__":
    main()
