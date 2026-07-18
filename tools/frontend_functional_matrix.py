#!/usr/bin/env python3
"""Functional matrix against MUFFIN legacy frontend endpoints.

This intentionally drives /MUFFIN/... routes, the same compatibility surface
used by the browser. It uses the API only to obtain the same JWT that the login
page stores in localStorage.
"""

from __future__ import annotations

import html
import json
import os
import re
import statistics
import time
import unicodedata
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


API_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
FRONTEND_URL = os.getenv("MUFFIN_FRONTEND_URL", "http://frontend:8501").rstrip("/")
USERNAME = os.getenv("MUFFIN_TEST_USERNAME") or os.getenv("BOOTSTRAP_ADMIN_USERNAME", "")
PASSWORD = os.getenv("MUFFIN_TEST_PASSWORD") or os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
RUN_ID = os.getenv("MUFFIN_TEST_RUN_ID") or datetime.now().strftime("QA%Y%m%d%H%M%S")
LIMIT = int(os.getenv("MUFFIN_TEST_LIMIT", "0") or "0")
REPORT_PATH = Path(os.getenv("MUFFIN_TEST_REPORT", f"/tmp/muffin_frontend_matrix_{RUN_ID}.json"))

CULTURE_RESULT_CODES = ("NEGATIVO", "POSITIVO", "NO_TRAJO_MUESTRA", "MUESTRA_INADECUADA")
GRAM_CODES = ("COCOS_GRAM_POSITIVOS", "BACILOS_GRAM_NEGATIVOS", "LEVADURAS")
NITRITE_CODES = ("", "NEGATIVO", "POSITIVO", "NO_APLICA")
COLONY_CODES = (
    "001000",
    "002000",
    "003000",
    "004000",
    "005000",
    "006000",
    "007000",
    "008000",
    "009000",
    "010000",
    "020000",
    "030000",
    "040000",
    "050000",
    "060000",
    "070000",
    "080000",
    "090000",
    "100000",
)
VALIDATION_MODES = (0, 1, 2)  # Guardar, validacion preliminar, validacion final.
TARGET_ORGANISMS = (
    "ESCHERICHIA COLI",
    "PROTEUS SP.",
    "KLEBSIELLA PNEUMONIAE",
    "STAPHYLOCOCCUS AUREUS",
)
TARGET_MANUAL_ANTIBIOTICS = (
    "FLUCONAZOL",
    "VORICONAZOL",
)


class FrontendError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class Client:
    def __init__(self) -> None:
        self.token = ""
        self.timings: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        auth: bool = True,
        expect_json: bool = True,
        timeout: int = 30,
    ) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers: dict[str, str] = {}
        if payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        started = time.perf_counter()
        try:
            with urlopen(Request(url, data=body, headers=headers, method=method), timeout=timeout) as response:
                raw = response.read()
                elapsed = time.perf_counter() - started
                self.timings.append({"method": method, "url": url, "status": response.status, "seconds": elapsed})
                if not expect_json:
                    return raw.decode("utf-8", errors="replace")
                return json.loads(raw.decode("utf-8")) if raw else None
        except HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - started
            self.timings.append({"method": method, "url": url, "status": error.code, "seconds": elapsed})
            raise FrontendError(f"HTTP {error.code} {url}", status=error.code, body=raw) from error
        except URLError as error:
            elapsed = time.perf_counter() - started
            self.timings.append({"method": method, "url": url, "status": "URLERROR", "seconds": elapsed})
            raise FrontendError(f"Network error {url}: {error}") from error

    def login(self) -> None:
        if not USERNAME or not PASSWORD:
            raise RuntimeError("MUFFIN_TEST_USERNAME/PASSWORD or BOOTSTRAP_ADMIN_USERNAME/PASSWORD are required.")
        response = self.request(
            "POST",
            f"{API_URL}/auth/login",
            payload={"username": USERNAME, "password": PASSWORD},
            auth=False,
        )
        self.token = response["access_token"]

    def front_get(self, path: str, query: dict[str, str] | None = None, *, expect_json: bool = True) -> Any:
        url = f"{FRONTEND_URL}{path}"
        if query:
            url += "?" + urlencode(query)
        return self.request("GET", url, expect_json=expect_json)

    def front_post(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", f"{FRONTEND_URL}{path}", payload=payload)


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value.upper()).strip()


def label_from_param_html(markup: str) -> str:
    match = re.search(r"<label[^>]*>(.*?)</label>", markup or "", flags=re.I | re.S)
    text = match.group(1) if match else markup
    text = re.sub(r"<[^>]+>", " ", text)
    return normalized(html.unescape(text))


def require_ok(response: dict[str, Any], context: str) -> None:
    if not isinstance(response, dict) or not response.get("resultado", False):
        raise FrontendError(f"{context}: {response.get('mensaje') if isinstance(response, dict) else response!r}")


def catalog(client: Client, path: str) -> list[dict[str, Any]]:
    payload = client.front_get(path)
    data = payload.get("data", []) if isinstance(payload, dict) else []
    if not data:
        raise FrontendError(f"Catalogo vacio: {path}")
    return data


def fetch_catalogs(client: Client) -> dict[str, Any]:
    origins = catalog(client, "/MUFFIN/Mic_procedencia/Obtener")
    services = catalog(client, "/MUFFIN/Mic_servicio/Obtener")
    clinicians = catalog(client, "/MUFFIN/Mic_medico/Obtener")
    exams = catalog(client, "/MUFFIN/Mic_examen/Obtener")
    panels = catalog(client, "/MUFFIN/Mic_orga_panel/Obtener")
    colony_panel_counts = catalog(client, "/MUFFIN/Mic_res_panel_recuento/Obtener")
    organisms = catalog(client, "/MUFFIN/Mic_orga/Obtener")

    specimen_pairs: list[dict[str, Any]] = []
    for exam in exams:
        rows = client.front_get("/MUFFIN/Mic_muestra_examen/ObtenerEXA", {"EXA": exam["examen_id"]}).get("data", [])
        for row in rows:
            specimen = row.get("oMic_muestra") or {}
            selectable = specimen.get("muestra_seleccionable", True)
            if selectable in {False, "False", "false", 0, "0"}:
                continue
            specimen_pairs.append({"exam": exam, "specimen": specimen})

    if not specimen_pairs:
        raise FrontendError("No se encontraron relaciones examen-muestra terminales.")

    organisms_by_name = {normalized(item.get("orga_desc", "")): item for item in organisms}
    representative_organisms = []
    for name in TARGET_ORGANISMS:
        found = organisms_by_name.get(normalized(name))
        if found:
            representative_organisms.append(found)
    if not representative_organisms:
        representative_organisms = organisms[:4]

    representative_antibiotics: list[dict[str, Any]] = []
    for name in TARGET_MANUAL_ANTIBIOTICS:
        rows = client.front_get("/MUFFIN/Mic_antibiotico/Obtener", {"search": name, "page_size": "20"}).get("data", [])
        exact = next((row for row in rows if normalized(row.get("atb_desc", "")) == normalized(name)), None)
        if exact:
            representative_antibiotics.append(exact)
    if len(representative_antibiotics) < len(TARGET_MANUAL_ANTIBIOTICS):
        rows = client.front_get("/MUFFIN/Mic_antibiotico/Obtener", {"page_size": "50"}).get("data", [])
        for row in rows:
            if row not in representative_antibiotics:
                representative_antibiotics.append(row)
            if len(representative_antibiotics) >= 2:
                break

    return {
        "origins": origins,
        "services": services,
        "clinicians": clinicians,
        "exams": exams,
        "panels": panels,
        "colony_panel_counts": colony_panel_counts,
        "organisms": representative_organisms,
        "manual_antibiotics": representative_antibiotics[:2],
        "specimen_pairs": specimen_pairs,
    }


def create_order(client: Client, *, index: int, origin: dict[str, Any], service: dict[str, Any], clinician: dict[str, Any]) -> dict[str, str]:
    hc = f"{RUN_ID}-HC-{index:04d}"
    sex = ("M", "F", "X")[index % 3]
    payload = {
        "objeto": {
            "orden_id": "",
            "oMic_persona": {
                "persona_hc": hc,
                "persona_apellidos": f"QA MATRIZ {index:04d}",
                "persona_nombres": f"PACIENTE {RUN_ID}",
                "persona_fecha_nac": f"{1980 + (index % 30):04d}-{(index % 12) + 1:02d}-{(index % 27) + 1:02d}",
                "persona_genero": sex,
            },
            "orden_fecha": datetime.now().strftime("%Y-%m-%d"),
            "orden_numero": "AUTOGEN",
            "orden_estado": True,
            "orden_comentarios": f"QA FUNCIONAL {RUN_ID}: {origin['procedencia_desc']} / {service['servicio_desc']}",
            "oMic_procedencia": {"procedencia_id": origin["procedencia_id"]},
            "oMic_servicio": {"servicio_id": service["servicio_id"]},
            "oMic_medico": {"medico_id": clinician["medico_id"]},
        }
    }
    response = client.front_post("/MUFFIN/Mic_orden/Guardar", payload)
    require_ok(response, "guardar orden")
    return {"order_id": response["orden_id"], "order_number": response.get("orden_numero", ""), "hc": hc}


def add_received_item(
    client: Client,
    *,
    order_id: str,
    specimen_pair: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    payload = {
        "objeto": {
            "oMic_orden": {"orden_id": order_id},
            "oMic_examen": {"examen_id": specimen_pair["exam"]["examen_id"]},
            "orden_det_codebar": "",
            "orden_det_muestra_comentarios": f"QA MUESTRA {RUN_ID} {index:04d}",
            "oMic_muestra": {"muestra_id": specimen_pair["specimen"]["muestra_cod_alfa"]},
            "fecha_muestra_toma": now,
            "fecha_muestra_recepcion": now,
        }
    }
    response = client.front_post("/MUFFIN/Mic_orden_detalle/RegistrarExaMuestraMic_orden_detalle", payload)
    require_ok(response, "agregar examen/muestra")
    details = client.front_get("/MUFFIN/Mic_orden_detalle/Obtener_Mic_orden_detalle_examen", {"orden_id": order_id}).get("data", [])
    if not details:
        raise FrontendError("La orden no devolvio detalles despues de agregar muestra.")
    return details[-1]


def result_values_for_case(case_index: int, positive_index: int = 0) -> dict[str, str]:
    result_code = CULTURE_RESULT_CODES[case_index % len(CULTURE_RESULT_CODES)]
    positive = result_code == "POSITIVO"
    return {
        "RESULTADO DEL CULTIVO": result_code,
        "OBSERVACIONES": f"QA RESULTADO {RUN_ID} CASO {case_index:04d}",
        "COLORACION GRAM": GRAM_CODES[positive_index % len(GRAM_CODES)] if positive else "",
        "PRUEBA DE NITRITO": NITRITE_CODES[positive_index % len(NITRITE_CODES)] if positive else "",
        "RECUENTO DE COLONIAS": COLONY_CODES[positive_index % len(COLONY_CODES)] if positive else "",
    }


def save_result(client: Client, *, item_id: str, case_index: int, positive_index: int, validation_mode: int) -> None:
    form = client.front_get("/MUFFIN/Mic_orden_detalle_res/ObtenerOrdenId", {"orden_det_id": item_id})
    rows = form.get("data", [])
    if len(rows) < 5:
        raise FrontendError(f"Formulario de resultados incompleto: {len(rows)} controles.")
    values_by_label = result_values_for_case(case_index, positive_index)
    control_ids: list[str] = []
    control_values: list[str] = []
    for row in rows:
        control_id = row.get("param_cod", "")
        label = label_from_param_html(row.get("param_html", ""))
        value = ""
        for expected_label, expected_value in values_by_label.items():
            if expected_label in label:
                value = expected_value
                break
        control_ids.append(control_id)
        control_values.append(value)
    response = client.front_post(
        "/MUFFIN/Mic_orden_detalle_res/Guardar",
        {
            "objeto": {
                "orden_det_id": item_id,
                "temporal1": "|".join(control_ids) + "|",
                "temporal2": "|".join(control_values) + "|",
                "other1": validation_mode,
                "other2": USERNAME,
            }
        },
    )
    require_ok(response, f"guardar resultado modo {validation_mode}")


def register_ast_if_needed(
    client: Client,
    *,
    item: dict[str, Any],
    case_index: int,
    positive_index: int,
    catalogs: dict[str, Any],
) -> None:
    if CULTURE_RESULT_CODES[case_index % len(CULTURE_RESULT_CODES)] != "POSITIVO":
        return
    panels = catalogs["panels"]
    organisms = catalogs["organisms"]
    if not panels or not organisms:
        return
    panel = panels[positive_index % len(panels)]
    organism = organisms[positive_index % len(organisms)]
    barcode = item["orden_det_codebar"]
    item_id = item["orden_det_id"]
    response = client.front_post(
        "/MUFFIN/Mic_res_panel/Registrar",
        {
            "objeto": {
                "item_id": item_id,
                "respanel_codebar": barcode,
                "panel_id": panel["orga_panel_id"],
                "organism_id": organism["orga_id_id"],
            }
        },
    )
    require_ok(response, "registrar aislado/panel AST")
    isolates = client.front_get("/MUFFIN/Mic_res_panel/ObtenerCodebar", {"codebar": barcode}).get("data", [])
    if not isolates:
        raise FrontendError("No se encontro aislado despues de registrar panel AST.")
    isolate = isolates[-1]
    isolate_id = isolate["respanel_id"]
    panel_without_default_antibiotics = "SIN ATB" in normalized(panel.get("orga_panel_desc", ""))
    manual_antibiotics = catalogs.get("manual_antibiotics", [])
    if panel_without_default_antibiotics and manual_antibiotics and (positive_index // max(len(panels), 1)) % 2 == 1:
        for antibiotic_index, antibiotic in enumerate(manual_antibiotics):
            response = client.front_post(
                "/MUFFIN/Mic_res_panel_detalle/GuardarManual",
                {
                    "objeto": {
                        "isolate_id": isolate_id,
                        "antibiotic_id": antibiotic["atb_id_id"],
                        "interpretation": ("S", "R")[antibiotic_index % 2],
                    }
                },
            )
            require_ok(response, "agregar antibiotico manual a panel sin ATB")
    ast_rows = client.front_get(
        "/MUFFIN/Mic_res_panel_detalle/ObtenerCodebarOrgaCod",
        {"codebar": barcode, "organismo_cod": isolate_id},
    ).get("data", [])
    colony_options = catalogs["colony_panel_counts"]
    colony_id = colony_options[case_index % len(colony_options)]["panel_res_recuento_id"] if colony_options else ""
    response = client.front_post(
        "/MUFFIN/Mic_res_panel_detalle/Guardar",
        {
            "objeto": {
                "oMic_res_panel": {
                    "oMic_orden_detalle": {"orden_det_id": item_id},
                    "respanel_id": isolate_id,
                    "respanel_organismo_cod": isolate_id,
                    "respanel_recuento": colony_id,
                    "respanel_organismo_comentario": f"QA AST {RUN_ID}",
                    "respanel_organismo_fenotipo": "",
                },
                "respaneldet_anti_cod_all": "|".join(row["respaneldet_anti_cod"] for row in ast_rows) + ("|" if ast_rows else ""),
                "respaneldet_anti_cmi_all": "|".join("1" if idx % 3 == 0 else "-" for idx, _row in enumerate(ast_rows)) + ("|" if ast_rows else ""),
                "respaneldet_anti_inter_all": "|".join(("S", "I", "R")[idx % 3] for idx, _row in enumerate(ast_rows)) + ("|" if ast_rows else ""),
                "respaneldet_anti_estado_all": "|".join("true" if idx == 0 and ast_rows else "false" for idx, _row in enumerate(ast_rows)) + ("|" if ast_rows else ""),
                "respaneldet_anti_metodologia_all": "|".join("CMI" if idx % 3 == 0 else "DISCO" for idx, _row in enumerate(ast_rows)) + ("|" if ast_rows else ""),
            }
        },
    )
    require_ok(response, "guardar identificacion/antibiograma")


def report_latency(timings: list[dict[str, Any]]) -> dict[str, Any]:
    seconds = [entry["seconds"] for entry in timings]
    if not seconds:
        return {}
    p95_index = max(0, int(len(seconds) * 0.95) - 1)
    return {
        "calls": len(seconds),
        "avg_seconds": round(statistics.mean(seconds), 4),
        "p95_seconds": round(sorted(seconds)[p95_index], 4),
        "max_seconds": round(max(seconds), 4),
        "slowest": sorted(timings, key=lambda item: item["seconds"], reverse=True)[:10],
    }


def main() -> None:
    client = Client()
    started = time.perf_counter()
    failures: list[dict[str, Any]] = []
    created: list[dict[str, Any]] = []
    coverage: dict[str, set[str]] = {
        "origins": set(),
        "services": set(),
        "exams": set(),
        "specimens": set(),
        "culture_results": set(),
        "gram": set(),
        "nitrite": set(),
        "colony_counts": set(),
        "validation_modes": set(),
        "ast_panels": set(),
        "organisms": set(),
        "manual_antibiotics": set(),
    }

    client.login()
    catalogs = fetch_catalogs(client)
    clinician = catalogs["clinicians"][0]
    cases = list(product(catalogs["origins"], catalogs["services"]))
    if LIMIT:
        cases = cases[:LIMIT]

    positive_count = 0
    for index, (origin, service) in enumerate(cases, start=1):
        specimen_pair = catalogs["specimen_pairs"][(index - 1) % len(catalogs["specimen_pairs"])]
        validation_mode = VALIDATION_MODES[(index - 1) % len(VALIDATION_MODES)]
        result_code = CULTURE_RESULT_CODES[(index - 1) % len(CULTURE_RESULT_CODES)]
        positive_index = positive_count if result_code == "POSITIVO" else 0
        try:
            order = create_order(client, index=index, origin=origin, service=service, clinician=clinician)
            item = add_received_item(client, order_id=order["order_id"], specimen_pair=specimen_pair, index=index)
            register_ast_if_needed(client, item=item, case_index=index - 1, positive_index=positive_index, catalogs=catalogs)
            save_result(
                client,
                item_id=item["orden_det_id"],
                case_index=index - 1,
                positive_index=positive_index,
                validation_mode=validation_mode,
            )
            if validation_mode == 2:
                html_report = client.front_get(
                    "/MUFFIN/Trans_pdf/Download_res_es",
                    {"orden_id": order["order_id"]},
                    expect_json=False,
                )
                if "Reporte de resultados" not in html_report and "Hospital Sub Regional" not in html_report:
                    raise FrontendError("Reporte final no contiene encabezado esperado.")
            created.append(
                {
                    "index": index,
                    "hc": order["hc"],
                    "order_number": order["order_number"],
                    "order_id": order["order_id"],
                    "item_id": item["orden_det_id"],
                    "barcode": item["orden_det_codebar"],
                    "origin": origin["procedencia_desc"],
                    "service": service["servicio_desc"],
                    "exam": specimen_pair["exam"]["examen_desc"],
                    "specimen": specimen_pair["specimen"]["muestra_desc"],
                    "result": result_code,
                    "validation_mode": validation_mode,
                }
            )
            coverage["origins"].add(origin["procedencia_desc"])
            coverage["services"].add(service["servicio_desc"])
            coverage["exams"].add(specimen_pair["exam"]["examen_desc"])
            coverage["specimens"].add(specimen_pair["specimen"]["muestra_desc"])
            coverage["culture_results"].add(result_code)
            coverage["validation_modes"].add(str(validation_mode))
            if result_code == "POSITIVO":
                values = result_values_for_case(index - 1, positive_index)
                coverage["gram"].add(values["COLORACION GRAM"])
                coverage["nitrite"].add(values["PRUEBA DE NITRITO"] or "(VACIO)")
                coverage["colony_counts"].add(values["RECUENTO DE COLONIAS"])
                if catalogs["panels"]:
                    coverage["ast_panels"].add(catalogs["panels"][positive_index % len(catalogs["panels"])]["orga_panel_desc"])
                if catalogs["organisms"]:
                    coverage["organisms"].add(catalogs["organisms"][positive_index % len(catalogs["organisms"])]["orga_desc"])
                if (
                    catalogs["panels"]
                    and "SIN ATB" in normalized(catalogs["panels"][positive_index % len(catalogs["panels"])]["orga_panel_desc"])
                    and catalogs.get("manual_antibiotics")
                    and (positive_index // max(len(catalogs["panels"]), 1)) % 2 == 1
                ):
                    coverage["manual_antibiotics"].update(item["atb_desc"] for item in catalogs["manual_antibiotics"])
        except Exception as exc:  # noqa: BLE001 - keep the matrix running.
            failures.append(
                {
                    "index": index,
                    "origin": origin.get("procedencia_desc"),
                    "service": service.get("servicio_desc"),
                    "exam": specimen_pair["exam"].get("examen_desc"),
                    "specimen": specimen_pair["specimen"].get("muestra_desc"),
                    "error": str(exc),
                    "status": getattr(exc, "status", None),
                    "body": getattr(exc, "body", "")[:1000],
                }
            )
        finally:
            if result_code == "POSITIVO":
                positive_count += 1
            if index % 25 == 0 or index == len(cases):
                print(
                    json.dumps(
                        {
                            "progress": f"{index}/{len(cases)}",
                            "created": len(created),
                            "failures": len(failures),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

    elapsed = time.perf_counter() - started
    summary = {
        "run_id": RUN_ID,
        "frontend_url": FRONTEND_URL,
        "api_url": API_URL,
        "elapsed_seconds": round(elapsed, 2),
        "requested_cases": len(cases),
        "created_cases": len(created),
        "failures": failures,
        "coverage": {key: sorted(value) for key, value in coverage.items()},
        "catalog_counts": {
            "origins": len(catalogs["origins"]),
            "services": len(catalogs["services"]),
            "exams": len(catalogs["exams"]),
            "exam_specimen_pairs": len(catalogs["specimen_pairs"]),
            "ast_panels": len(catalogs["panels"]),
            "representative_organisms": len(catalogs["organisms"]),
            "representative_manual_antibiotics": len(catalogs["manual_antibiotics"]),
        },
        "created_sample": created[:10],
        "created_tail": created[-10:],
        "latency": report_latency(client.timings),
    }
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "run_id": RUN_ID,
        "created_cases": len(created),
        "failed_cases": len(failures),
        "report": str(REPORT_PATH),
        "latency": summary["latency"],
    }, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
