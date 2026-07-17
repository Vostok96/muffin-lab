"""Black-box catalog checks for a running local Docker environment."""

import json
import os
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


def find_by_code(path: str, code: str, token: str, *, active_only: bool = True) -> dict:
    page = request(f"{path}?search={code}&active_only={'true' if active_only else 'false'}", token=token)
    return next(item for item in page["data"] if item["code"] == code)


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the catalog smoke test.")

    admin_login = request("/auth/login", method="POST", payload={"username": "dev-admin", "password": PASSWORD})
    entry_login = request("/auth/login", method="POST", payload={"username": "dev-entry", "password": PASSWORD})
    admin_token = admin_login["access_token"]
    entry_token = entry_login["access_token"]

    area = find_by_code("/catalogs/areas", "MICROBIOLOGY", entry_token)
    assert find_by_code("/catalogs/origins", "HOSPITALIZACION", entry_token)
    assert find_by_code("/catalogs/services", "EMERGENCIA", entry_token)
    assert find_by_code("/catalogs/clinicians", "DEV-CLINICIAN", entry_token)
    assert find_by_code("/catalogs/containers", "CONTENEDOR_PROTOCOLO", entry_token)
    assert find_by_code("/catalogs/specimen-types", "URO_CHORRO_MEDIO", entry_token)
    assert find_by_code("/catalogs/exams", "URINE_CULTURE", entry_token)
    assert find_by_code("/catalogs/parameters", "CULTURE_RESULT", entry_token)

    suffix = uuid4().hex[:8].upper()
    origin_code = f"ORIGEN_{suffix}"
    service_code = f"SERVICIO_{suffix}"
    clinician_code = f"MED_{suffix}"
    container_code = f"CONT_{suffix}"
    specimen_code = f"MUESTRA_{suffix}"
    exam_code = f"EXAMEN_{suffix}"
    parameter_code = f"PARAMETRO_{suffix}"

    origin = request(
        "/catalogs/origins",
        method="POST",
        payload={"code": origin_code.lower(), "name": "ORIGEN DE PRUEBA"},
        token=admin_token,
    )
    assert origin["code"] == origin_code
    service = request("/catalogs/services", method="POST", payload={"code": service_code, "name": "SERVICIO DE PRUEBA"}, token=admin_token)
    clinician = request(
        "/catalogs/clinicians",
        method="POST",
        payload={
            "code": clinician_code,
            "family_name": "PRUEBA",
            "given_name": "MEDICO",
            "email": "prueba@example.invalid",
        },
        token=admin_token,
    )
    container = request(
        "/catalogs/containers",
        method="POST",
        payload={"code": container_code, "name": "CONTENEDOR DE PRUEBA"},
        token=admin_token,
    )
    specimen = request(
        "/catalogs/specimen-types",
        method="POST",
        payload={"code": specimen_code, "name": "MUESTRA DE PRUEBA", "container_id": container["id"]},
        token=admin_token,
    )
    exam = request(
        "/catalogs/exams",
        method="POST",
        payload={
            "code": exam_code,
            "name": "EXAMEN DE PRUEBA",
            "external_code": f"EXT-{suffix}",
            "barcode_suffix": suffix[:4],
            "laboratory_area_id": area["id"],
            "sends_to_analyzer": False,
            "requires_colony_count": True,
        },
        token=admin_token,
    )
    parameter = request(
        "/catalogs/parameters",
        method="POST",
        payload={
            "code": parameter_code,
            "name": "RESULTADO DE PRUEBA",
            "section": "MICROBIOLOGY",
            "value_type": "SELECT",
            "options_schema": ["NEGATIVO", "POSITIVO"],
            "is_active": True,
        },
        token=admin_token,
    )

    specimen_relation_path = f"/catalogs/exams/{exam['id']}/specimen-types/{specimen['id']}"
    request(specimen_relation_path, method="PUT", payload={"is_favorite": True}, token=admin_token)
    specimen_links = request(f"/catalogs/exams/{exam['id']}/specimen-types", token=entry_token)
    assert specimen_links == [{"exam_id": exam["id"], "specimen_type_id": specimen["id"], "is_favorite": True}]
    request(specimen_relation_path, method="DELETE", token=admin_token)
    request(specimen_relation_path, method="PUT", payload={"is_favorite": True}, token=admin_token)

    parameter_relation_path = f"/catalogs/exams/{exam['id']}/parameters/{parameter['id']}"
    request(
        parameter_relation_path,
        method="PUT",
        payload={"display_order": 1, "external_code": f"RESULTADO-{suffix}", "is_required": True},
        token=admin_token,
    )
    parameter_links = request(f"/catalogs/exams/{exam['id']}/parameters", token=entry_token)
    assert parameter_links[0]["parameter_definition_id"] == parameter["id"]
    request(parameter_relation_path, method="DELETE", token=admin_token)
    request(
        parameter_relation_path,
        method="PUT",
        payload={"display_order": 1, "external_code": f"RESULTADO-{suffix}", "is_required": True},
        token=admin_token,
    )

    request(f"/catalogs/origins/{origin['id']}", method="PATCH", payload={"is_active": False}, token=admin_token)
    assert not any(item["code"] == origin_code for item in request(f"/catalogs/origins?search={origin_code}", token=entry_token)["data"])
    assert find_by_code("/catalogs/origins", origin_code, entry_token, active_only=False)["is_active"] is False

    expect_status(409, "/catalogs/services", "POST", {"code": service_code, "name": "DUPLICADO"}, admin_token)
    expect_status(403, "/catalogs/services", "POST", {"code": f"DENEGADO_{suffix}", "name": "DENEGADO"}, entry_token)

    for path, item in (
        ("/catalogs/services", service),
        ("/catalogs/clinicians", clinician),
        ("/catalogs/exams", exam),
        ("/catalogs/parameters", parameter),
        ("/catalogs/specimen-types", specimen),
        ("/catalogs/containers", container),
    ):
        request(f"{path}/{item['id']}", method="PATCH", payload={"is_active": False}, token=admin_token)

    audit_events = request("/admin/audit-events", token=admin_token)
    assert any(event["entity_id"] == exam["id"] for event in audit_events)
    print("Catalog API smoke test passed.")


if __name__ == "__main__":
    main()
