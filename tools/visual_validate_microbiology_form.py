#!/usr/bin/env python3
"""Headless visual validation for MUFFIN microbiology results.

The script intentionally uses Chrome DevTools Protocol directly so it can run
without Playwright/Selenium. It targets the local fictitious worklist row and
cleans up the temporary isolate it creates.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import random
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import websockets


BASE_URL = os.environ.get("MUFFIN_BASE_URL", "http://127.0.0.1:8877")
TARGET_HC = os.environ.get("MUFFIN_VISUAL_TARGET_HC", "DEV-HC-0001")
SCREENSHOT_DIR = Path(os.environ.get("MUFFIN_VISUAL_OUT", "/tmp"))
REPORT_PATH = SCREENSHOT_DIR / "muffin_visual_validation_report.json"


class CdpSession:
    def __init__(self, websocket_url: str) -> None:
        self.websocket_url = websocket_url
        self.next_id = 1
        self.ws: Any = None

    async def __aenter__(self) -> "CdpSession":
        self.ws = await websockets.connect(self.websocket_url, max_size=32 * 1024 * 1024)
        return self

    async def __aexit__(self, *_exc: object) -> None:
        if self.ws is not None:
            await self.ws.close()

    async def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        command_id = self.next_id
        self.next_id += 1
        payload: dict[str, Any] = {"id": command_id, "method": method}
        if params is not None:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))
        while True:
            message = json.loads(await self.ws.recv())
            if message.get("id") == command_id:
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                return message.get("result", {})

    async def evaluate(self, expression: str, await_promise: bool = False) -> Any:
        result = await self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
                "userGesture": True,
            },
        )
        remote = result.get("result", {})
        if "exceptionDetails" in result:
            raise RuntimeError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
        return remote.get("value")

    async def wait_for(self, label: str, expression: str, timeout: float = 20.0) -> Any:
        deadline = time.monotonic() + timeout
        last_value: Any = None
        while time.monotonic() < deadline:
            try:
                last_value = await self.evaluate(expression, await_promise=True)
                if last_value:
                    return last_value
            except Exception as exc:  # noqa: BLE001 - report the last useful failure.
                last_value = str(exc)
            await asyncio.sleep(0.25)
        raise TimeoutError(f"Timed out waiting for {label}; last value: {last_value!r}")

    async def screenshot(self, path: Path) -> None:
        data = await self.send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        path.write_bytes(base64.b64decode(data["data"]))


def fetch_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def start_chrome() -> tuple[subprocess.Popen[Any], str, tempfile.TemporaryDirectory[str]]:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("Chrome executable not found")

    profile_dir = tempfile.TemporaryDirectory(prefix="muffin-chrome-")
    port = random.randint(43000, 49000)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-sandbox",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir.name}",
        "about:blank",
    ]
    log_path = SCREENSHOT_DIR / "muffin_visual_chrome.log"
    log_file = log_path.open("wb")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    list_url = f"http://127.0.0.1:{port}/json/list"
    deadline = time.monotonic() + 10
    websocket_url = ""
    while time.monotonic() < deadline:
        try:
            targets = fetch_json(list_url)
            page = next((target for target in targets if target.get("type") == "page"), None)
            if page and page.get("webSocketDebuggerUrl"):
                websocket_url = page["webSocketDebuggerUrl"]
                break
        except Exception:
            pass
        time.sleep(0.2)
    if not websocket_url:
        proc.terminate()
        profile_dir.cleanup()
        raise RuntimeError(f"Could not connect to Chrome DevTools; see {log_path}")
    return proc, websocket_url, profile_dir


async def run_validation() -> dict[str, Any]:
    proc, websocket_url, profile_dir = start_chrome()
    created_isolate = ""
    report: dict[str, Any] = {
        "base_url": BASE_URL,
        "target_hc": TARGET_HC,
        "screenshots": [],
        "checks": {},
    }
    try:
        async with CdpSession(websocket_url) as page:
            await page.send("Page.enable")
            await page.send("Runtime.enable")
            await page.send(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
            )

            await page.send("Page.navigate", {"url": f"{BASE_URL}/MUFFIN/Login/Index"})
            await page.wait_for("login page", "document.readyState === 'complete' && !!document.querySelector('#login-form')")
            await page.evaluate(
                """
                (() => {
                    document.querySelector('#username').value = 'admin';
                    document.querySelector('#password').value = 'admin';
                    document.querySelector('#login-form').dispatchEvent(
                        new Event('submit', { bubbles: true, cancelable: true })
                    );
                    return true;
                })()
                """
            )
            await page.wait_for(
                "authenticated session",
                "localStorage.getItem('muffin_token') && location.pathname === '/MUFFIN/'",
                timeout=15,
            )
            report["checks"]["login"] = "ok"

            await page.send("Page.navigate", {"url": f"{BASE_URL}/MUFFIN/Mic_orden_detalle/Resultado_microbiologia"})
            await page.wait_for(
                "results page datatable",
                """
                !!window.jQuery && !!$.fn.DataTable && $.fn.DataTable.isDataTable('#tbdata')
                """,
                timeout=20,
            )
            await page.wait_for(
                "initial worklist rows",
                "$('#tbdata').DataTable().rows().data().toArray().length > 0",
                timeout=20,
            )
            await page.evaluate(
                f"""
                (() => {{
                    $('#txtBuscar').val({json.dumps(TARGET_HC)});
                    $('#btnBuscar').trigger('click');
                    return true;
                }})()
                """
            )
            await page.wait_for(
                "filtered fictitious worklist row",
                f"""
                (() => {{
                    if (!$.fn.DataTable.isDataTable('#tbdata')) return false;
                    const rows = $('#tbdata').DataTable().rows().data().toArray();
                    return rows.length === 1 && rows[0].oMic_orden.oMic_persona.persona_hc === {json.dumps(TARGET_HC)};
                }})()
                """,
                timeout=20,
            )
            worklist_shot = SCREENSHOT_DIR / "muffin_visual_worklist_filtered.png"
            await page.screenshot(worklist_shot)
            report["screenshots"].append(str(worklist_shot))
            report["checks"]["worklist_filter"] = "ok"

            await page.evaluate(
                """
                (() => {
                    const row = $('#tbdata').DataTable().rows().data().toArray()[0];
                    rec_abrirPopUpForm_ini(row.orden_det_id);
                    return row.orden_det_codebar;
                })()
                """
            )
            await page.wait_for(
                "result modal loaded",
                """
                $('#FormModal').hasClass('show')
                    && $('#txtCodigoBarras').val()
                    && $('#divListaParama').text().includes('Resultado Parámetros')
                """,
                timeout=20,
            )
            modal_shot = SCREENSHOT_DIR / "muffin_visual_result_modal_initial.png"
            await page.screenshot(modal_shot)
            report["screenshots"].append(str(modal_shot))
            report["checks"]["result_modal"] = await page.evaluate(
                """
                (() => ({
                    barcodePresent: !!$('#txtCodigoBarras').val(),
                    careSetting: $('#cboTipoLocalizacion').val(),
                    addPanelVisible: $('#btnOPAdpanel').is(':visible'),
                    preliminaryVisible: $('#btnValPreliminar').is(':visible'),
                    finalVisible: $('#btnValFinal').is(':visible')
                }))()
                """
            )

            await page.evaluate("$('#btnOPAdpanel').trigger('click')")
            await page.wait_for(
                "add panel modal options",
                """
                $('#FormModalTer').hasClass('show')
                    && $('#cboPanelLista option').length >= 7
                    && $('#cboOrgaLista option').length > 0
                """,
                timeout=20,
            )
            panel_catalog = await page.evaluate(
                """
                (() => Array.from(document.querySelectorAll('#cboPanelLista option')).map(option => option.textContent.trim()))()
                """
            )
            report["checks"]["panel_catalog"] = panel_catalog

            await page.evaluate(
                """
                (() => {
                    $('#txtBuscarOrgaLista').val('ESCHERICHIA COLI').trigger('input');
                    return true;
                })()
                """
            )
            await page.wait_for(
                "organism search results",
                """
                Array.from(document.querySelectorAll('#cboOrgaLista option'))
                    .some(option => option.textContent.trim().toUpperCase() === 'ESCHERICHIA COLI')
                """,
                timeout=20,
            )
            add_panel_shot = SCREENSHOT_DIR / "muffin_visual_add_panel_search.png"
            await page.screenshot(add_panel_shot)
            report["screenshots"].append(str(add_panel_shot))
            report["checks"]["organism_search"] = "ESCHERICHIA COLI found"

            await page.evaluate(
                """
                (() => {
                    window.__muffinPanelRegister = null;
                    $(document).one('ajaxComplete.muffinVisualPanelRegister', function (_event, xhr, settings) {
                        if (settings && settings.url && settings.url.includes('/Mic_res_panel/Registrar')) {
                            let body = xhr.responseText || '';
                            try { body = JSON.parse(body); } catch (_error) {}
                            window.__muffinPanelRegister = { status: xhr.status, response: body };
                        }
                    });
                    const panel = Array.from(document.querySelectorAll('#cboPanelLista option'))
                        .find(option => option.textContent.includes('PANEL AST-N401'));
                    const organism = Array.from(document.querySelectorAll('#cboOrgaLista option'))
                        .find(option => option.textContent.trim().toUpperCase() === 'ESCHERICHIA COLI');
                    if (!panel || !organism) return false;
                    $('#cboPanelLista').val(panel.value).trigger('change');
                    $('#cboOrgaLista').val(organism.value).trigger('change');
                    $('#btnAddPanelGuardar').trigger('click');
                    return true;
                })()
                """
            )
            report["checks"]["panel_register_response"] = await page.wait_for(
                "panel register response",
                "window.__muffinPanelRegister",
                timeout=20,
            )
            try:
                await page.wait_for(
                    "AST table loaded after panel add",
                    """
                    !$('#FormModalTer').hasClass('show')
                        && $('#div_iden_atb').is(':visible')
                        && $('#IDEN_ORGA').val().toUpperCase().includes('ESCHERICHIA COLI')
                        && $('#tlbtbody_atb tr').length >= 15
                    """,
                    timeout=20,
                )
            except Exception:
                report["checks"]["post_add_debug"] = await page.evaluate(
                    """
                    (() => ({
                        panelModalShown: $('#FormModalTer').hasClass('show'),
                        panelModalDisplay: $('#FormModalTer').css('display'),
                        idAstVisible: $('#div_iden_atb').is(':visible'),
                        organismField: $('#IDEN_ORGA').val(),
                        isolateField: $('#IDEN_PANEL_ID').val(),
                        organismOptions: $('#cboMicroOrganismos option').length,
                        astRows: $('#tlbtbody_atb tr').length,
                        registerResponse: window.__muffinPanelRegister,
                        swalText: $('.sweet-alert:visible').text().trim()
                    }))()
                    """
                )
                debug_shot = SCREENSHOT_DIR / "muffin_visual_post_add_failure.png"
                await page.screenshot(debug_shot)
                report["screenshots"].append(str(debug_shot))
                cleanup_after_failure = await page.evaluate(
                    """
                    (async () => {
                        const codebar = $('#txtCodigoBarras').val();
                        const itemId = $('#txtIdOrdenDet').val();
                        if (!codebar || !itemId) return { skipped: true, reason: 'missing codebar or item id' };
                        const lookup = await new Promise(resolve => {
                            $.ajax({
                                url: $.MisUrls.url._ObtenerCodebarMic_res_panel + '?codebar=' + encodeURIComponent(codebar),
                                type: 'GET',
                                dataType: 'json',
                                success: resolve,
                                error: xhr => resolve({ resultado: false, status: xhr.status })
                            });
                        });
                        const isolateId = lookup && lookup.data && lookup.data[0] && lookup.data[0].respanel_id;
                        if (!isolateId) return { lookup, deleted: false };
                        const deleted = await new Promise(resolve => {
                            $.ajax({
                                url: $.MisUrls.url._EliminarMic_res_panel
                                    + '?respanel_id=' + encodeURIComponent(isolateId)
                                    + '&item_id=' + encodeURIComponent(itemId),
                                type: 'GET',
                                dataType: 'json',
                                success: resolve,
                                error: xhr => resolve({ resultado: false, status: xhr.status })
                            });
                        });
                        return { lookupCount: lookup.data.length, isolateId, deleted };
                    })()
                    """,
                    await_promise=True,
                )
                report["checks"]["cleanup_after_failure"] = cleanup_after_failure
                raise
            created_isolate = await page.evaluate("$('#IDEN_PANEL_ID').val()")
            ast_shot = SCREENSHOT_DIR / "muffin_visual_ast_table.png"
            await page.screenshot(ast_shot)
            report["screenshots"].append(str(ast_shot))
            report["checks"]["ast_table"] = await page.evaluate(
                """
                (() => ({
                    organism: $('#IDEN_ORGA').val(),
                    isolateIdPresent: !!$('#IDEN_PANEL_ID').val(),
                    rows: $('#tlbtbody_atb tr').length,
                    headers: Array.from(document.querySelectorAll('#div_iden_atb table thead th'))
                        .map(th => th.textContent.trim()),
                    interpretations: Array.from(document.querySelectorAll('#tlbtbody_atb select.clInter'))
                        .slice(0, 5)
                        .map(select => select.value),
                    methods: Array.from(document.querySelectorAll('#tlbtbody_atb select.clMetodol'))
                        .slice(0, 5)
                        .map(select => select.value),
                    buttons: {
                        addAntibiotic: $('#btnAddATB').is(':visible'),
                        deletePanel: $('#btnDeletePanel').is(':visible'),
                        save: $('#btnGuardarCambios').is(':visible'),
                        preliminary: $('#btnValPreliminar').is(':visible'),
                        final: $('#btnValFinal').is(':visible')
                    }
                }))()
                """
            )

            if not created_isolate:
                raise RuntimeError("A panel was added visually, but no isolate id was rendered")

            delete_result = await page.evaluate(
                """
                (async () => {
                    const isolateId = $('#IDEN_PANEL_ID').val();
                    const itemId = $('#txtIdOrdenDet').val();
                    const url = $.MisUrls.url._EliminarMic_res_panel
                        + '?respanel_id=' + encodeURIComponent(isolateId)
                        + '&item_id=' + encodeURIComponent(itemId);
                    return await new Promise(resolve => {
                        $.ajax({
                            url,
                            type: 'GET',
                            dataType: 'json',
                            contentType: 'application/json; charset=utf-8',
                            success: resolve,
                            error: xhr => resolve({ resultado: false, status: xhr.status })
                        });
                    });
                })()
                """,
                await_promise=True,
            )
            report["checks"]["cleanup_delete_response"] = delete_result
            await page.evaluate("cboMicroOrganismosCODEBAR($('#txtCodigoBarras').val())")
            await page.wait_for(
                "temporary isolate removed",
                """
                !$('#div_iden_atb').is(':visible') && $('#cboMicroOrganismos option').length === 0
                """,
                timeout=20,
            )
            report["checks"]["cleanup"] = "ok"
            report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        profile_dir.cleanup()
    return report


def main() -> None:
    report = asyncio.run(run_validation())
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
