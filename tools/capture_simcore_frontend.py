from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "mirror"
PAGES_DIR = MIRROR / "_pages"
DOCS = ROOT / "docs"

BASE_URL = os.environ.get("SIMCORE_SOURCE_URL", "http://192.168.0.220/SIMCORE_WEB/")
USER = os.environ.get("SIMCORE_SOURCE_USER", "")
PASSWORD = os.environ.get("SIMCORE_SOURCE_PASS", "")
HEADERS = {"User-Agent": "Mozilla/5.0"}

PAGES = [
    "Login/Index",
    "Home/Index",
    "Mic_persona/",
    "Mic_procedencia/",
    "Mic_servicio/",
    "Mic_medico/",
    "Mic_res_comentarios_def/",
    "Mic_area/",
    "Mic_examen/",
    "Mic_muestra/",
    "Mic_muestra_contenedor/",
    "Mic_parametro/",
    "mic_orga_panel/",
    "Mic_res_panel_recuento/",
    "Mic_orga/",
    "Mic_antibiotico/",
    "Mic_usuario/",
    "Mic_destinos/",
    "Mic_seccion/",
    "Mic_configuracion_general/",
    "Mic_orden/",
    "Mic_destinos_orden_detalle/",
    "Mic_orden_detalle/Resultado_microbiologia",
    "Trans_consultas/Microbiologia_pac_orden",
    "Trans_consultas/Microbiologia_proce_servi_medico",
    "Trans_reportes/Microbiologia_rep_produccion",
    "Trans_reportes/Microbiologia_rep_idt_ast",
    "Trans_reportes/Microbiologia_rep_botellas",
    "Trans_reportes/Microbiologia_rep_etiquetas_gen",
    "Trans_reportes/Microbiologia_rep_hoja_trabajo",
]


def clean_route(route: str) -> str:
    route = route.strip()
    if route.startswith("~/"):
        route = route[2:]
    return route.lstrip("/")


def safe_name(path: str) -> str:
    path = path.strip("/")
    if not path:
        return "index"
    path = path.replace("/", "__")
    path = re.sub(r"[^A-Za-z0-9_.-]+", "_", path)
    return path


def local_asset_path(url: str) -> Path:
    parsed = urlparse(url)
    rel = parsed.path.lstrip("/")
    return MIRROR / rel


def normalize_url(value: str, current_url: str) -> str | None:
    value = (value or "").strip()
    if not value or value.startswith("#") or value.lower().startswith("javascript:"):
        return None
    if value.startswith("~/"):
        value = "/SIMCORE_WEB/" + value[2:]
    return urljoin(current_url, value)


def find_assets(html: str) -> set[str]:
    assets = set()
    patterns = [
        r"<script[^>]+src=[\"']([^\"']+)",
        r"<link[^>]+href=[\"']([^\"']+)",
        r"<img[^>]+src=[\"']([^\"']+)",
    ]
    for pattern in patterns:
        assets.update(re.findall(pattern, html, flags=re.I))
    return assets


def find_css_urls(text: str) -> set[str]:
    found = set()
    for raw in re.findall(r"url\(([^)]+)\)", text, flags=re.I):
        raw = raw.strip().strip("'\"")
        if raw and not raw.startswith("data:"):
            found.add(raw)
    return found


def find_endpoints(text: str) -> dict[str, str]:
    endpoints = {}
    for key, url in re.findall(r"(_[A-Za-z0-9_]+)\s*:\s*[\"']([^\"']+)[\"']", text):
        if "/SIMCORE_WEB/" in url:
            endpoints[key] = url
    return endpoints


def write_bytes(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def fetch_asset(session: requests.Session, asset_url: str, fetched: set[str]) -> tuple[str, int, int] | None:
    parsed = urlparse(asset_url)
    if parsed.netloc and parsed.netloc != urlparse(BASE_URL).netloc:
        return None
    if not parsed.path.startswith("/SIMCORE_WEB/"):
        return None
    key = parsed._replace(query="").geturl()
    if key in fetched:
        return None
    fetched.add(key)

    response = session.get(asset_url, headers=HEADERS, timeout=30)
    if response.status_code >= 400:
        return response.status_code, response.headers.get("content-type", ""), 0
    path = local_asset_path(asset_url)
    write_bytes(path, response.content)
    return response.status_code, response.headers.get("content-type", ""), len(response.content)


def main() -> None:
    if not USER or not PASSWORD:
        raise SystemExit("Define SIMCORE_SOURCE_USER y SIMCORE_SOURCE_PASS antes de recapturar.")

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    login_url = urljoin(BASE_URL, "Login/Index")
    session.post(login_url, data={"user": USER, "pass": PASSWORD}, headers=HEADERS, timeout=30)

    page_map: dict[str, str] = {}
    assets: set[str] = set()
    endpoints: dict[str, str] = {}
    fetched_assets: set[str] = set()
    page_report = []
    page_errors = []

    for route in PAGES:
        clean = clean_route(route)
        url = urljoin(BASE_URL, clean)
        response = session.get(url, headers=HEADERS, timeout=30)
        if response.status_code >= 400:
            page_errors.append({"route": "/SIMCORE_WEB/" + clean, "status": response.status_code, "url": url})
            continue
        html_bytes = response.content
        html = html_bytes.decode(response.encoding or "utf-8", errors="replace")
        page_file = PAGES_DIR / f"{safe_name('/SIMCORE_WEB/' + clean)}.html"
        write_bytes(page_file, html_bytes)

        request_path = "/SIMCORE_WEB/" + clean
        page_map[request_path.rstrip("/")] = str(page_file.relative_to(ROOT)).replace("\\", "/")
        page_map[request_path if request_path.endswith("/") else request_path + "/"] = str(page_file.relative_to(ROOT)).replace("\\", "/")
        if clean == "Home/Index":
            page_map["/SIMCORE_WEB/"] = str(page_file.relative_to(ROOT)).replace("\\", "/")

        for asset in find_assets(html):
            normalized = normalize_url(asset, url)
            if normalized:
                assets.add(normalized)
        endpoints.update(find_endpoints(html))
        page_report.append({"route": request_path, "status": response.status_code, "bytes": len(html_bytes)})

    # Fetch HTML-declared assets and then one CSS-relative layer.
    css_to_scan = []
    asset_report = []
    asset_errors = []
    for asset in sorted(assets):
        result = fetch_asset(session, asset, fetched_assets)
        if not result:
            continue
        status, ctype, size = result
        if status >= 400:
            asset_errors.append({"url": asset, "status": status})
            continue
        asset_report.append({"url": asset, "content_type": ctype, "bytes": size})
        if "css" in ctype or "/Content/" in urlparse(asset).path:
            css_to_scan.append(asset)

    for css_url in css_to_scan:
        css_path = local_asset_path(css_url)
        if not css_path.exists():
            continue
        css_text = css_path.read_text(encoding="utf-8", errors="replace")
        for ref in find_css_urls(css_text):
            normalized = normalize_url(ref, css_url)
            if normalized:
                result = fetch_asset(session, normalized, fetched_assets)
                if result:
                    status, ctype, size = result
                    if status >= 400:
                        asset_errors.append({"url": normalized, "status": status})
                        continue
                    asset_report.append({"url": normalized, "content_type": ctype, "bytes": size})

    manifest = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "source_base_url": BASE_URL,
        "pages": page_map,
        "page_count": len(page_report),
        "page_errors": page_errors,
        "asset_count": len(asset_report),
        "asset_errors": asset_errors,
    }
    (DOCS / "capture_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (DOCS / "routes.json").write_text(json.dumps(page_report, indent=2, ensure_ascii=False), encoding="utf-8")
    (DOCS / "assets.json").write_text(json.dumps(asset_report, indent=2, ensure_ascii=False), encoding="utf-8")
    (DOCS / "endpoints.json").write_text(json.dumps(endpoints, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    report = [
        "# Captura SIMCORE WEB",
        "",
        f"Origen: `{BASE_URL}`",
        f"Paginas capturadas: {len(page_report)}",
        f"Paginas con error: {len(page_errors)}",
        f"Assets capturados: {len(asset_report)}",
        f"Assets con error: {len(asset_errors)}",
        f"Endpoints detectados: {len(endpoints)}",
        "",
        "No se invocaron endpoints de listados de pacientes/ordenes; solo paginas y assets publicos autenticados.",
    ]
    if page_errors:
        report.extend(["", "## Paginas con error", ""])
        for item in page_errors:
            report.append(f"- `{item['route']}` -> HTTP {item['status']}")
    if asset_errors:
        report.extend(["", "## Assets con error", ""])
        for item in asset_errors:
            report.append(f"- `{item['url']}` -> HTTP {item['status']}")
    (DOCS / "CAPTURE_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(page_report), "page_errors": len(page_errors), "assets": len(asset_report), "asset_errors": len(asset_errors), "endpoints": len(endpoints)}, indent=2))


if __name__ == "__main__":
    main()
