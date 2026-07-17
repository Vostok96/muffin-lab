"""Black-box microbiology (isolates and AST) workflow checks."""

import json
import os
from datetime import datetime
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
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
    page = request(path, token=token)
    return next(item for item in page["data"] if item["code"] == code)


def catalog_item_or_none(path: str, code: str, token: str) -> dict | None:
    separator = "&" if "?" in path else "?"
    page = request(
        f"{path}{separator}active_only=false&search={quote(code, safe='')}&page_size=100",
        token=token,
    )
    return next((item for item in page["data"] if item["code"] == code), None)


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set before running the microbiology smoke test.")

    admin_token = login("dev-admin")
    entry_token = login("dev-entry")
    processor_token = login("dev-processor")

    # --- Seeded data verification ---

    seeded_order = request("/orders?search=DEV-ORDER-0001", token=processor_token)["data"][0]
    item = seeded_order["items"][0]
    result_data = request(f"/order-items/{item['id']}/result", token=processor_token)
    assert result_data["status"] == "RESULT_SAVED"
    result_id = result_data["id"]

    isolates = request(f"/results/{result_id}/isolates", token=processor_token)
    assert len(isolates) == 1
    seeded_isolate = isolates[0]
    assert seeded_isolate["organism_id"] is not None
    assert seeded_isolate["ast_panel_id"] is not None
    ars = request(f"/isolates/{seeded_isolate['id']}/antimicrobial-results", token=processor_token)
    assert len(ars) == 5

    # Historical collection/reception corrections remain historical.
    original_collection_at = item["collection_at"]
    original_received_at = item["received_at"]
    corrected_item = request(
        f"/order-items/{item['id']}/specimen-details",
        method="PATCH",
        payload={
            "collection_at": "2026-07-13T08:30:00-05:00",
            "received_at": "2026-07-14T09:15:00-05:00",
            "location": "AMBULATORIO",
        },
        token=processor_token,
    )
    assert corrected_item["collection_at"].startswith("2026-07-13")
    assert corrected_item["received_at"].startswith("2026-07-14")
    request(
        f"/order-items/{item['id']}/specimen-details",
        method="PATCH",
        payload={
            "collection_at": original_collection_at,
            "received_at": original_received_at,
            "location": None,
        },
        token=processor_token,
    )

    # --- Catalog verification ---

    for catalog, code in [
        ("/catalogs/organisms", "ECOLI"),
        ("/catalogs/organisms", "KPN"),
        ("/catalogs/colony-count-options", "001000"),
        ("/catalogs/colony-count-options", "100001"),
        ("/catalogs/defined-comments", "MIXED_FLORA"),
        ("/catalogs/antibiotics", "AMK"),
        ("/catalogs/antibiotics", "CIP"),
        ("/catalogs/ast-panels", "AST-N401"),
    ]:
        entry = catalog_item(catalog, code, processor_token)
        if "is_active" in entry:
            assert entry["is_active"] is True
        else:
            assert entry["code"] == code

    # --- Organism CRUD ---

    organism = catalog_item("/catalogs/organisms", "ECOLI", processor_token)
    # Entry users cannot create catalogs
    expect_status(403, "/catalogs/organisms", "POST", entry_token, {"code": "NEW_ORG", "name": "New organism"})
    # ADMIN creates an organism
    new_organism = catalog_item_or_none("/catalogs/organisms", "PRUEBA-ORG", admin_token)
    if new_organism:
        new_organism = request(
            f"/catalogs/organisms/{new_organism['id']}",
            method="PATCH",
            payload={"is_active": True},
            token=admin_token,
        )
    else:
        new_organism = request(
            "/catalogs/organisms",
            method="POST",
            payload={"code": "PRUEBA-ORG", "name": "ORGANISMO DE PRUEBA"},
            token=admin_token,
        )
    assert new_organism["code"] == "PRUEBA-ORG"
    # PATCH to deactivate
    updated = request(
        f"/catalogs/organisms/{new_organism['id']}",
        method="PATCH",
        payload={"is_active": False},
        token=admin_token,
    )
    assert updated["is_active"] is False

    # --- AST panel antibiotics ---

    panel = catalog_item("/catalogs/ast-panels", "AST-N401", processor_token)
    panel_antibiotics = request(f"/catalogs/ast-panels/{panel['id']}/antibiotics", token=processor_token)
    assert len(panel_antibiotics) == 15
    # Add a new antibiotic to the panel
    new_abx = catalog_item_or_none("/catalogs/antibiotics", "PRUEBA-ATB", admin_token)
    if new_abx:
        new_abx = request(
            f"/catalogs/antibiotics/{new_abx['id']}",
            method="PATCH",
            payload={"is_active": True},
            token=admin_token,
        )
    else:
        new_abx = request(
            "/catalogs/antibiotics",
            method="POST",
            payload={"code": "PRUEBA-ATB", "name": "ANTIBIOTICO DE PRUEBA"},
            token=admin_token,
        )
    link = request(
        f"/catalogs/ast-panels/{panel['id']}/antibiotics/{new_abx['id']}",
        method="PUT",
        payload={"display_order": 99, "default_method": "DIFUSION EN DISCO"},
        token=admin_token,
    )
    assert link["display_order"] == 99
    # Remove the antibiotic from the panel
    request(
        f"/catalogs/ast-panels/{panel['id']}/antibiotics/{new_abx['id']}",
        method="DELETE",
        token=admin_token,
    )
    panel_antibiotics_after = request(f"/catalogs/ast-panels/{panel['id']}/antibiotics", token=processor_token)
    assert len(panel_antibiotics_after) == len(panel_antibiotics)

    # --- Isolate CRUD ---

    kpn_organism = catalog_item("/catalogs/organisms", "KPN", processor_token)
    rare_cco = catalog_item("/catalogs/colony-count-options", "001000", processor_token)

    # Entry user cannot create isolates
    expect_status(403, f"/results/{result_id}/isolates", "POST", entry_token, {
        "organism_id": kpn_organism["id"],
    })
    # Create a second isolate
    isolate2 = request(
        f"/results/{result_id}/isolates",
        method="POST",
        payload={
            "organism_id": kpn_organism["id"],
            "colony_count_option_id": rare_cco["id"],
            "phenotype": "NO FERMENTADOR DE LACTOSA",
            "comment": "SEGUNDO AISLADO PARA PRUEBA.",
        },
        token=processor_token,
    )
    assert isolate2["organism_id"] == kpn_organism["id"]
    assert isolate2["result_id"] == result_id
    isolate2_ars = request(f"/isolates/{isolate2['id']}/antimicrobial-results", token=processor_token)
    assert len(isolate2_ars) == 0  # No AST panel assigned

    # Update isolate to add AST panel (autofill)
    updated_isolate = request(
        f"/results/{result_id}/isolates/{isolate2['id']}",
        method="PATCH",
        payload={"ast_panel_id": panel["id"]},
        token=processor_token,
    )
    assert updated_isolate["ast_panel_id"] == panel["id"]
    isolate2_ars = request(f"/isolates/{isolate2['id']}/antimicrobial-results", token=processor_token)
    assert len(isolate2_ars) == 15  # Autofilled from panel

    # --- Antimicrobial result editing ---

    ar_to_edit = isolate2_ars[0]
    updated_ar = request(
        f"/isolates/{isolate2['id']}/antimicrobial-results/{ar_to_edit['id']}",
        method="PATCH",
        payload={"mic_value": ">=64", "interpretation": "R"},
        token=processor_token,
    )
    assert updated_ar["mic_value"] == ">=64"
    assert updated_ar["interpretation"] == "R"

    # Entry user cannot edit antimicrobial results
    expect_status(
        403,
        f"/isolates/{isolate2['id']}/antimicrobial-results/{ar_to_edit['id']}",
        "PATCH",
        entry_token,
        {"interpretation": "S"},
    )
    # Validate interpretation constraint
    expect_status(
        422,
        f"/isolates/{isolate2['id']}/antimicrobial-results/{ar_to_edit['id']}",
        "PATCH",
        processor_token,
        {"interpretation": "INVALID"},
    )

    # --- Isolate deletion (ADMIN only) ---

    # Create a temporary isolate for deletion test
    temp_isolate = request(
        f"/results/{result_id}/isolates",
        method="POST",
        payload={"organism_id": organism["id"]},
        token=processor_token,
    )
    # Processor cannot delete
    expect_status(403, f"/results/{result_id}/isolates/{temp_isolate['id']}", "DELETE", processor_token)
    # ADMIN deletes
    request(f"/results/{result_id}/isolates/{temp_isolate['id']}", method="DELETE", token=admin_token)

    # List isolates after deletion
    final_isolates = request(f"/results/{result_id}/isolates", token=processor_token)
    assert len(final_isolates) == 2  # seeded + isolate2

    # --- Audit verification ---
    audits = request("/admin/audit-events", token=admin_token)
    audit_actions = {event["action"] for event in audits}
    assert "CREATE" in audit_actions
    assert "UPDATE" in audit_actions
    assert "DELETE" in audit_actions
    isolate_audits = [event for event in audits if event["entity_type"] == "isolate"]
    assert len(isolate_audits) >= 3

    request(f"/results/{result_id}/isolates/{isolate2['id']}", method="DELETE", token=admin_token)
    request(
        f"/catalogs/antibiotics/{new_abx['id']}",
        method="PATCH",
        payload={"is_active": False},
        token=admin_token,
    )

    # Final validation locks isolates and AST until the result is reopened.
    request(f"/order-items/{item['id']}/result/preliminary-validation", method="POST", token=admin_token)
    request(f"/order-items/{item['id']}/result/final-validation", method="POST", token=admin_token)
    expect_status(
        409,
        f"/isolates/{seeded_isolate['id']}/antimicrobial-results/{ars[0]['id']}",
        "PATCH",
        processor_token,
        {"interpretation": "R"},
    )
    request(
        f"/order-items/{item['id']}/result/reopen",
        method="POST",
        payload={"reason": "REAPERTURA AUTOMATICA DE LA PRUEBA"},
        token=admin_token,
    )

    print("Microbiology advanced smoke test passed.")


if __name__ == "__main__":
    main()
