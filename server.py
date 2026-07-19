from __future__ import annotations

import html
import json
import mimetypes
import os
import copy
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from email.utils import formatdate
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request as URLRequest, urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent
MIRROR = ROOT / "mirror"
MANIFEST = ROOT / "docs" / "capture_manifest.json"


def env_text(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def project_path(value: str | None, default: Path) -> Path:
    raw = (value or "").strip()
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def image_path(value: str | None, default: Path, fallback: Path) -> Path:
    path = project_path(value, default)
    return path if path.exists() else fallback


DEFAULT_CLIENT_ROOT = ROOT / "CLIENTES" / "_plantilla"
if "andahuaylas" in env_text("DEFAULT_INSTITUTION_NAME", "").lower():
    DEFAULT_CLIENT_ROOT = ROOT / "CLIENTES" / "Hospital Sub Regional Andahuaylas"

INSTITUTION_NAME = env_text(
    "MUFFIN_INSTITUTION_NAME",
    env_text("DEFAULT_INSTITUTION_NAME", "MUFFIN Microbiología Hospitalaria"),
)
INSTITUTION_SLUG = env_text(
    "MUFFIN_INSTITUTION_SLUG",
    env_text("DEFAULT_INSTITUTION_SLUG", "muffin-padre"),
)
PRODUCT_NAME = env_text("MUFFIN_PRODUCT_NAME", "MUFFIN Microbiología Hospitalaria")
PRODUCT_TAGLINE = env_text(
    "MUFFIN_PRODUCT_TAGLINE",
    "Microbiología: Unidad de Fuentes, Flujos e Informes Nosocomiales",
)
PRODUCT_OWNER = env_text("MUFFIN_IP_OWNER", "RyM SAC")
COPYRIGHT_OWNER = env_text("MUFFIN_COPYRIGHT_OWNER", INSTITUTION_NAME)
APP_VERSION = env_text("MUFFIN_VERSION", "1.0")
CLIENT_ROOT = project_path(os.environ.get("MUFFIN_CLIENT_ROOT"), DEFAULT_CLIENT_ROOT)
PRODUCT_IMAGE = image_path(os.environ.get("MUFFIN_PRODUCT_IMAGE"), ROOT / "MUFFIN_ICONO.jpg", ROOT / "MUFFIN_ICONO.jpg")
BRAND_IMAGE = image_path(
    os.environ.get("MUFFIN_BRAND_IMAGE"),
    CLIENT_ROOT / "logo.png",
    CLIENT_ROOT / "logo andahuylas.png" if (CLIENT_ROOT / "logo andahuylas.png").exists() else PRODUCT_IMAGE,
)
MASCOT_IMAGE = image_path(os.environ.get("MUFFIN_MASCOT_IMAGE"), ROOT / "MUFFIN_SINFONDO.png", PRODUCT_IMAGE)


def load_client_signers() -> tuple[dict, ...]:
    config_path = project_path(os.environ.get("MUFFIN_SIGNERS_CONFIG"), CLIENT_ROOT / "signers.json")
    if not config_path.exists():
        return ()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    items = payload.get("signers", payload) if isinstance(payload, dict) else payload
    signers: list[dict] = []
    if not isinstance(items, list):
        return ()
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug", "")).strip()
        name = str(item.get("name", "")).strip()
        file_value = item.get("file") or item.get("signature_file")
        if not slug or not name or not file_value:
            continue
        file_path = Path(str(file_value))
        if not file_path.is_absolute():
            file_path = CLIENT_ROOT / file_path
        usernames = item.get("usernames") or ()
        if isinstance(usernames, str):
            usernames = [usernames]
        signers.append(
            {
                "slug": slug,
                "usernames": tuple(str(username).strip() for username in usernames if str(username).strip()),
                "name": name,
                "title": str(item.get("title", "")).strip(),
                "credential": str(item.get("credential", "")).strip(),
                "file": file_path,
            }
        )
    return tuple(signers)


CLIENT_SIGNERS = load_client_signers()
SIGNATURE_IMAGE_ROUTES = {f"/MUFFIN/firmas/{signer['slug']}.jpeg": signer["file"] for signer in CLIENT_SIGNERS}
GRAM_RESULT_OPTIONS = [
    ("COCOS_GRAM_POSITIVOS", "COCOS GRAM POSITIVOS"),
    ("BACILOS_GRAM_NEGATIVOS", "BACILOS GRAM NEGATIVOS"),
    ("LEVADURAS", "LEVADURAS"),
]
COLONY_COUNT_RESULT_OPTIONS = [
    ("001000", "1,000 UFC/mL"),
    ("002000", "2,000 UFC/mL"),
    ("003000", "3,000 UFC/mL"),
    ("004000", "4,000 UFC/mL"),
    ("005000", "5,000 UFC/mL"),
    ("006000", "6,000 UFC/mL"),
    ("007000", "7,000 UFC/mL"),
    ("008000", "8,000 UFC/mL"),
    ("009000", "9,000 UFC/mL"),
    ("010000", "10,000 UFC/mL"),
    ("020000", "20,000 UFC/mL"),
    ("030000", "30,000 UFC/mL"),
    ("040000", "40,000 UFC/mL"),
    ("050000", "50,000 UFC/mL"),
    ("060000", "60,000 UFC/mL"),
    ("070000", "70,000 UFC/mL"),
    ("080000", "80,000 UFC/mL"),
    ("090000", "90,000 UFC/mL"),
    ("100000", "100,000 UFC/mL"),
]
RESULT_PARAMETER_OPTION_OVERRIDES = {
    "CULTURE_GRAM": GRAM_RESULT_OPTIONS,
    "CULTURE_COLONY_COUNT": COLONY_COUNT_RESULT_OPTIONS,
}
SUPPRESSED_RESULT_PARAMETERS = {"CULTURE_ANTIMICROBIAL_ACTIVITY"}
CODE39_PATTERNS = {
    "0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnnn", "4": "nnnwwnnnw",
    "5": "wnnwwnnnn", "6": "nnwwwnnnn", "7": "nnnwnnwnw", "8": "wnnwnnwnn", "9": "nnwwnnwnn",
    "A": "wnnnnwnnw", "B": "nnwnnwnnw", "C": "wnwnnwnnn", "D": "nnnnwwnnw", "E": "wnnnwwnnn",
    "F": "nnwnwwnnn", "G": "nnnnnwwnw", "H": "wnnnnwwnn", "I": "nnwnnwwnn", "J": "nnnnwwwnn",
    "K": "wnnnnnnww", "L": "nnwnnnnww", "M": "wnwnnnnwn", "N": "nnnnwnnww", "O": "wnnnwnnwn",
    "P": "nnwnwnnwn", "Q": "nnnnnnwww", "R": "wnnnnnwwn", "S": "nnwnnnwwn", "T": "nnnnwnwwn",
    "U": "wwnnnnnnw", "V": "nwwnnnnnw", "W": "wwwnnnnnn", "X": "nwnnwnnnw", "Y": "wwnnwnnnn",
    "Z": "nwwnwnnnn", "-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn", "$": "nwnwnwnnn",
    "/": "nwnwnnnwn", "+": "nwnnnwnwn", "%": "nnnwnwnwn", "*": "nwnnwnwnn",
}
FAVICON = ROOT / "MUFFIN_FAVICON.png"
FAVICON_MARKUP = b'\n\t<link rel="icon" type="image/png" sizes="256x256" href="/MUFFIN_FAVICON.png?v=muffin-20260716-v2">\n'
HOST = os.environ.get("SIMCORE_CLONE_HOST", "127.0.0.1")
PORT = int(os.environ.get("SIMCORE_CLONE_PORT", "8877"))
API_BASE = os.environ.get("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1")
API_CACHE_TTL_SECONDS = int(os.environ.get("MUFFIN_API_CACHE_TTL_SECONDS", "300"))
STATIC_CACHE_VERSIONED_SECONDS = int(os.environ.get("MUFFIN_STATIC_CACHE_VERSIONED_SECONDS", "2592000"))
STATIC_CACHE_UNVERSIONED_SECONDS = int(os.environ.get("MUFFIN_STATIC_CACHE_UNVERSIONED_SECONDS", "3600"))
API_GET_CACHE: dict[tuple[str, str, str], tuple[float, int, dict | list | None]] = {}
STATIC_CACHEABLE_PREFIXES = (
    "/MUFFIN/Content/",
    "/MUFFIN/Scripts/",
    "/MUFFIN/bundles/",
    "/MUFFIN/Imagenes/",
)
STATIC_CACHEABLE_SUFFIXES = {
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}
STATIC_CACHEABLE_DIRECT_PATHS = {
    "/favicon.ico",
    "/MUFFIN_FAVICON.png",
    "/MUFFIN_ICONO.jpg",
    "/MUFFIN_PRODUCTO.jpg",
    "/MUFFIN_MASCOTA.png",
}
STATIC_ASSET_ALIASES = {
    "/MUFFIN/Content/css.css": "/MUFFIN/Content/css",
    "/MUFFIN/bundles/jquery.js": "/MUFFIN/bundles/jquery",
    "/MUFFIN/Content/PluginsJS.js": "/MUFFIN/Content/PluginsJS",
}
FRONTEND_ASSET_VERSION = "andahuaylas-20260718-2"
LEGACY_CSS_VERSIONED_URL = (
    b"/MUFFIN/Content/css?v=ivzLv745bmnThkrYOWP2Oyh3EQaw__rxaWvN5bNa0zg1"
)
LEGACY_JQUERY_VERSIONED_URL = (
    b"/MUFFIN/bundles/jquery?v=8Oos0avDZyPg-cbyVzvkIfERIE1DGSe3sRQdCSYrgEQ1"
)
LEGACY_PLUGIN_JS_VERSIONED_URL = (
    b"/MUFFIN/Content/PluginsJS?v=sQB6J2EBUgtBNkJ6uHK2oNSgdLTnVwcEwKIRWaMhYlM1"
)

LOGIN_PAGE = ROOT / "docs" / "login.html"
LOGOUT_REDIRECT = b"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/MUFFIN/Login/Index"><title>Cerrando sesion...</title></head><body><script>localStorage.clear();window.location.href='/MUFFIN/Login/Index';</script></body></html>"""

THEME_TOGGLE_CSS = b"""<script>
(function(){
var h=document.documentElement,s=localStorage.getItem("muffin-theme");
if(s==="dark")h.setAttribute("data-theme","dark");
else if(!s&&window.matchMedia&&window.matchMedia("(prefers-color-scheme:dark)").matches)h.setAttribute("data-theme","dark");
})();
</script>
<style>
.theme-nav-item{display:flex;margin:.35rem 0 .55rem;width:100%}
.theme-pill{align-items:center;background:rgba(233,244,239,.11);border:1px solid rgba(223,238,232,.20);border-radius:.75rem;color:#edf6f2;cursor:pointer;display:grid;gap:.55rem;grid-template-columns:2rem minmax(0,1fr) auto;min-height:3rem;outline:none;padding:.45rem .55rem;text-align:left;transition:background .18s,border .18s,box-shadow .18s,color .18s;width:100%}
.theme-pill:hover,.theme-pill:focus{background:rgba(233,244,239,.16);border-color:rgba(223,238,232,.30);box-shadow:0 10px 22px rgba(6,48,58,.18);color:#edf6f2}
.theme-pill-icon{align-items:center;background:#d8e6df;border-radius:.55rem;box-shadow:0 6px 14px rgba(6,48,58,.14);color:#2f7778;display:inline-flex;font-size:.92rem;height:2rem;justify-content:center;width:2rem}
.theme-pill-copy{display:grid;gap:.06rem;line-height:1.1;min-width:0}
.theme-pill-title{font-size:.82rem;font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.theme-pill-state{background:rgba(233,244,239,.14);border:1px solid rgba(223,238,232,.18);border-radius:999px;color:#edf6f2;font-size:.66rem;font-weight:800;line-height:1;padding:.27rem .5rem;white-space:nowrap}
[data-theme=dark] .theme-pill{background:rgba(18,39,43,.68);border-color:rgba(92,174,169,.24);color:#d6e3de}
[data-theme=dark] .theme-pill:hover,[data-theme=dark] .theme-pill:focus{background:rgba(28,55,59,.78);border-color:rgba(92,174,169,.34)}
[data-theme=dark] .theme-pill-icon{background:#d6e3de;color:#274f52}
[data-theme=dark] .theme-pill-state{background:rgba(92,174,169,.16);border-color:rgba(92,174,169,.24);color:#d6e3de}
@media (min-width:992px){
body.muffin-sidebar-collapsed .theme-nav-item{justify-content:center;margin:.25rem 0 .45rem}
body.muffin-sidebar-collapsed .theme-pill{gap:0;grid-template-columns:1fr;height:44px;min-height:44px;padding:.35rem;width:44px}
body.muffin-sidebar-collapsed .theme-pill-copy,body.muffin-sidebar-collapsed .theme-pill-state{display:none}
body.muffin-sidebar-collapsed .theme-pill-icon{height:32px;width:32px}
}
@media (max-width:991.98px){
.theme-nav-item{margin:.2rem 0 .45rem}
.theme-pill{background:rgba(255,255,255,.10);grid-template-columns:2rem minmax(0,1fr) auto;max-width:22rem}
}
</style>"""

THEME_TOGGLE_SCRIPT = b"""<script>
(function(){
var h=document.documentElement;
function currentTheme(){return h.getAttribute("data-theme")==="dark"?"dark":"light";}
function setTheme(theme){
    h.setAttribute("data-theme",theme);
    localStorage.setItem("muffin-theme",theme);
    updateButton();
}
function updateButton(){
    var b=document.querySelector(".theme-pill");
    if(!b)return;
    var dark=currentTheme()==="dark";
    var iconBox=b.querySelector(".theme-pill-icon");
    var title=b.querySelector(".theme-pill-title");
    var state=b.querySelector(".theme-pill-state");
    if(iconBox)iconBox.innerHTML=dark?'<i class="fas fa-moon" aria-hidden="true"></i>':'<i class="fas fa-sun" aria-hidden="true"></i>';
    if(title)title.textContent="Tema";
    if(state)state.textContent=dark?"Oscuro":"Claro";
    b.setAttribute("aria-label",dark?"Cambiar a tema claro":"Cambiar a tema oscuro");
    b.setAttribute("title",dark?"Tema oscuro":"Tema claro");
}
function buildButton(){
    var b=document.createElement("button");
    b.type="button";
    b.className="theme-pill";
    b.innerHTML='<span class="theme-pill-icon" aria-hidden="true"><i class="fas fa-sun"></i></span><span class="theme-pill-copy"><span class="theme-pill-title">Tema</span></span><span class="theme-pill-state">Claro</span>';
    b.addEventListener("click",function(){setTheme(currentTheme()==="dark"?"light":"dark");});
    return b;
}
function mountButton(){
    if(document.querySelector(".theme-nav-item")){updateButton();return;}
    var target=document.querySelector(".muffin-nav .navbar-nav.ml-auto");
    var item=document.createElement("li");
    item.className="nav-item theme-nav-item";
    item.appendChild(buildButton());
    if(target)target.insertBefore(item,target.firstElementChild);
    else document.body.appendChild(item);
    updateButton();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mountButton);
else mountButton();
})();
</script>"""

# -- Global auto-uppercase for visible text fields and select labels --
UPPERCASE_SCRIPT = b"""<script>
(function(){
function uppercaseValue(event){
var el=event.currentTarget,start=el.selectionStart,end=el.selectionEnd;
var value=el.value.toLocaleUpperCase("es");
if(value===el.value)return;
el.value=value;
if(start!==null&&end!==null)el.setSelectionRange(start,end);
}
function uppercaseOptions(select){
Array.from(select.options).forEach(function(option){option.text=option.text.toLocaleUpperCase("es");});
}
function initUpper(root){
var scope=root&&root.querySelectorAll?root:document;
scope.querySelectorAll("form input[type=text].form-control,form textarea.form-control").forEach(function(el){
if(el.id==="txtEdad"||el.id==="txtNumeroOrden"||el.dataset.muffinUppercase)return;
el.dataset.muffinUppercase="true";
el.addEventListener("input",uppercaseValue);
});
scope.querySelectorAll("form select.form-control").forEach(uppercaseOptions);
var age=document.getElementById("txtEdad");
if(age){age.readOnly=true;age.setAttribute("aria-readonly","true");}
}
function start(){
initUpper(document);
new MutationObserver(function(mutations){
mutations.forEach(function(mutation){
mutation.addedNodes.forEach(function(node){
if(node.nodeType!==1)return;
if(node.tagName==="OPTION"&&node.parentElement)uppercaseOptions(node.parentElement);
else if(node.tagName==="SELECT")uppercaseOptions(node);
initUpper(node);
});
});
}).observe(document.body,{childList:true,subtree:true});
}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",start);}else{start();}
})();
</script>"""

APP_FOOTER_MARKUP = f"""		<footer class="muffin-footer" role="contentinfo">
			<div class="muffin-footer-brand">
				<span class="muffin-footer-mark" aria-hidden="true">
					<img src="/MUFFIN_ICONO.jpg?v={html.escape(INSTITUTION_SLUG, quote=True)}-{html.escape(APP_VERSION, quote=True)}" alt="">
				</span>
				<span class="muffin-footer-title">
					<strong>{html.escape(INSTITUTION_NAME)}</strong>
					<small>{html.escape(PRODUCT_NAME)}</small>
				</span>
			</div>
			<div class="muffin-footer-legal">
				<span>&copy; 2026 {html.escape(COPYRIGHT_OWNER)}.</span>
				<span>{html.escape(PRODUCT_NAME)}. Propiedad intelectual de {html.escape(PRODUCT_OWNER)}.</span>
			</div>
			<span class="muffin-footer-version">v{html.escape(APP_VERSION)}</span>
		</footer>""".encode("utf-8")

LEGACY_FOOTERS = [
    """		<footer>
			<p>Todos los derechos reservados &copy; MUFFIN v0.1.0<br />2026, Microbiolog&iacute;a Hospitalaria</p>
		</footer>""".encode("utf-8"),
    """		<footer>
			<p>Todos los derechos reservados &copy; MUFFIN v0.1.0<br />2026, Microbiología Hospitalaria</p>
		</footer>""".encode("utf-8"),
    "		<footer class=\"muffin-footer\">MUFFIN | Microbiología: Unidad de Fuentes, Flujos e Informes Nosocomiales</footer>".encode("utf-8"),
]


def apply_corporate_footer(body: bytes) -> bytes:
    for legacy_footer in LEGACY_FOOTERS:
        body = body.replace(legacy_footer, APP_FOOTER_MARKUP)
    return body


def apply_runtime_branding(body: bytes) -> bytes:
    replacements = (
        (b"Hospital Sub Regional de Andahuaylas", html_bytes(INSTITUTION_NAME)),
        (b"MUFFIN Microbiolog\xc3\xada Hospitalaria", html_bytes(PRODUCT_NAME)),
        (
            b"Microbiolog\xc3\xada: Unidad de Fuentes, Flujos e Informes Nosocomiales",
            html_bytes(PRODUCT_TAGLINE),
        ),
        (b"Propiedad intelectual de RyM SAC", f"Propiedad intelectual de {html.escape(PRODUCT_OWNER)}".encode("utf-8")),
        (b"&copy; 2026 RyM SAC.", f"&copy; 2026 {html.escape(PRODUCT_OWNER)}.".encode("utf-8")),
    )
    for old, new in replacements:
        body = body.replace(old, new)
    return body

# ── Session injection: reads JWT, calls /auth/me, updates navbar + menus ──

SESSION_SCRIPT = b"""<script>
(function(){
var API='/api/v1';
var token=localStorage.getItem('muffin_token');
if(!token){window.location.href='/MUFFIN/Login/Index';return;}
if(window.jQuery){jQuery.ajaxPrefilter(function(options,originalOptions,jqXHR){if(options.url&&options.url.indexOf('/MUFFIN/')===0)jqXHR.setRequestHeader('Authorization','Bearer '+token);});}

var shellBrandImg=document.querySelector('.muffin-nav .navbar-brand img');
if(shellBrandImg){
    shellBrandImg.src='/MUFFIN_PRODUCTO.jpg';
    shellBrandImg.alt='MUFFIN';
}

function cleanName(value){
    var namePrefixes=['DR','DRA','LIC','MG','MGR','MBA','BLGA','BLGO','MBLGA','MBLGO','ING','ABG','ABGA','MED'];
    var text=(value||'').toString().replace(/[.,]/g,' ').replace(/\\s+/g,' ').trim();
    var parts=text.split(' ').filter(Boolean);
    while(parts.length && namePrefixes.indexOf(parts[0].toUpperCase())!==-1){parts.shift();}
    return parts.join(' ').trim();
}

function syncDesktopSidebar(){
    var collapse=document.getElementById('navbarSupportedContent');
    var toggler=document.querySelector('.muffin-nav .navbar-toggler');
    if(!collapse||!toggler)return;
    if(window.matchMedia('(min-width: 992px)').matches){
        collapse.classList.add('show');
        var collapsed=localStorage.getItem('muffin-sidebar')==='collapsed';
        document.body.classList.toggle('muffin-sidebar-collapsed',collapsed);
        toggler.setAttribute('aria-expanded',collapsed?'false':'true');
    }else{
        document.body.classList.remove('muffin-sidebar-collapsed');
        collapse.classList.remove('show');
        toggler.setAttribute('aria-expanded','false');
    }
}

syncDesktopSidebar();
window.addEventListener('resize', syncDesktopSidebar);
var sidebarToggler=document.querySelector('.muffin-nav .navbar-toggler');
if(sidebarToggler){
    sidebarToggler.addEventListener('click',function(event){
        if(!window.matchMedia('(min-width: 992px)').matches)return;
        event.preventDefault();
        event.stopImmediatePropagation();
        var collapsed=!document.body.classList.contains('muffin-sidebar-collapsed');
        localStorage.setItem('muffin-sidebar',collapsed?'collapsed':'expanded');
        syncDesktopSidebar();
    },true);
}

fetch(API+'/auth/me',{headers:{'Authorization':'Bearer '+token}})
.then(function(r){
    if(!r.ok){localStorage.removeItem('muffin_token');window.location.href='/MUFFIN/Login/Index';return null;}
    return r.json();
})
.then(function(u){
    if(!u)return;
    var RM={ADMIN:1,PROCESS_ADMIN:2,PROCESSOR:3,ENTRY:4,CONSULTANT:5,COLLECTOR:6,CLINICIAN:7};
    var RN={1:'Administrador',2:'Admin Procesos',3:'Procesador',4:'Ingreso/Consultas',5:'Consultas',6:'Toma Muestras',7:'Medico'};
    var roleNum=RM[u.roles&&u.roles[0]]||7;

    var navLink=document.querySelector('.navbar-nav.ml-auto .nav-link.dropdown-toggle');
    if(navLink){
        var givenName=cleanName(u.given_name||'');
        var familyName=cleanName(u.family_name||'');
        var displayName=familyName&&givenName ? (familyName+', '+givenName) : (familyName||givenName);
        navLink.textContent='';
        var sessionSpan=document.createElement('span');
        sessionSpan.className='muffin-session-name';
        var sessionIcon=document.createElement('i');
        sessionIcon.className='fas fa-user-circle';
        sessionSpan.appendChild(sessionIcon);
        sessionSpan.appendChild(document.createTextNode(' '+displayName+' '));
        navLink.appendChild(sessionSpan);
        function hidden(id, value){
            var input=document.createElement('input');
            input.type='hidden';
            input.id=id;
            input.value=value;
            navLink.appendChild(input);
        }
        hidden('session_user_id', u.username);
        hidden('session_user_rol', roleNum);
        hidden('session_user_rol_validacion_preliminar', roleNum<=3?'True':'False');
        hidden('session_user_rol_validacion_final', roleNum<=2?'True':'False');
        navLink.title=displayName;
    }
    var jb=document.querySelector('.jumbotron .lead');
    if(jb){
        var headerGiven=cleanName(u.given_name||'');
        var headerFamily=cleanName(u.family_name||'');
        var headerName=headerFamily&&headerGiven ? (headerFamily+', '+headerGiven) : (headerFamily||headerGiven);
        jb.textContent=headerName;
    }

    document.querySelectorAll('.cl_permiso_proceso_configuracion,.cl_permiso_proceso_ordenes,.cl_permiso_proceso_verificacion,.cl_permiso_proceso_resultados,.cl_permiso_consultas,.cl_permiso_proceso_reportes').forEach(function(s){s.style.display='none';});

    /*  ROLES MUFFIN - Menu permissions by role
        1 ADMIN           : Config, Ordenes, Verificacion, Resultados, Consultas, Reportes
        2 PROCESS_ADMIN   : Ordenes, Verificacion, Resultados, Consultas, Reportes
        3 PROCESSOR       : Ordenes, Verificacion, Resultados, Consultas, Reportes
        4 ENTRY           : Ordenes, Verificacion, Consultas
        5 CONSULTANT      : Ordenes, Verificacion, Consultas
        6 COLLECTOR       : Verificacion, Consultas
        7 CLINICIAN       : Consultas
    */
    var RM2={
        1:['configuracion','ordenes','verificacion','resultados','consultas','reportes'],
        2:['ordenes','verificacion','resultados','consultas','reportes'],
        3:['ordenes','verificacion','resultados','consultas','reportes'],
        4:['ordenes','verificacion','consultas'],
        5:['ordenes','verificacion','consultas'],
        6:['verificacion','consultas'],
        7:['consultas']
    };
    var SM={configuracion:'.cl_permiso_proceso_configuracion',ordenes:'.cl_permiso_proceso_ordenes',verificacion:'.cl_permiso_proceso_verificacion',resultados:'.cl_permiso_proceso_resultados',consultas:'.cl_permiso_consultas',reportes:'.cl_permiso_proceso_reportes'};

    var menus=RM2[roleNum]||[];
    menus.forEach(function(m){var el=document.querySelector(SM[m]);if(el)el.style.display='';});
    if(!document.querySelector('.muffin-client-panel')){
        var menuList=document.querySelector('.muffin-nav .navbar-nav.mr-auto');
        var reportItem=document.querySelector('.muffin-nav .cl_permiso_proceso_reportes');
        if(menuList){
            var clientItem=document.createElement('li');
            clientItem.className='nav-item muffin-client-panel';
            clientItem.innerHTML='<img src="/MUFFIN_ICONO.jpg" alt=""><span class="muffin-client-kicker">Instituci&oacute;n</span><strong>Hospital Sub Regional de Andahuaylas</strong>';
            if(reportItem&&reportItem.parentNode===menuList)reportItem.insertAdjacentElement('afterend',clientItem);
            else menuList.appendChild(clientItem);
            var mascotItem=document.createElement('li');
            mascotItem.className='nav-item muffin-sidebar-mascot';
            mascotItem.innerHTML='<img src="/MUFFIN_MASCOTA.png" alt="Mascota MUFFIN">';
            clientItem.insertAdjacentElement('afterend',mascotItem);
        }
    }
})
.catch(function(){localStorage.removeItem('muffin_token');window.location.href='/MUFFIN/Login/Index';});
})();
</script>"""


def html_bytes(value: str) -> bytes:
    return html.escape(value, quote=True).encode("utf-8")


SESSION_SCRIPT = SESSION_SCRIPT.replace(b"Hospital Sub Regional de Andahuaylas", html_bytes(INSTITUTION_NAME))

# ── SIMCORE → MUFFIN proxy mappings ──

ROLE_MAP = {1: "ADMIN", 2: "PROCESS_ADMIN", 3: "PROCESSOR", 4: "ENTRY", 5: "CONSULTANT", 6: "COLLECTOR", 7: "CLINICIAN"}
ROLE_REV = {"ADMIN": 1, "PROCESS_ADMIN": 2, "PROCESSOR": 3, "ENTRY": 4, "CONSULTANT": 5, "COLLECTOR": 6, "CLINICIAN": 7}
CARE_SETTING_LABELS = {
    "AMBULATORIO": "AMBULATORIO",
    "INTERNADO_NO_UCI": "HOSPITALIZACION GENERAL",
    "CUIDADOS_INTERMEDIOS": "CUIDADOS INTERMEDIOS",
    "UCI": "CUIDADOS INTENSIVOS (UCI)",
    "URGENCIA": "URGENCIA",
    "DESCONOCIDO": "DESCONOCIDO",
}
LOCAL_TIMEZONE = timezone(timedelta(hours=-5))
NAME_PREFIXES = {
    "DR",
    "DRA",
    "LIC",
    "LIC.",
    "MG",
    "MGR",
    "MBA",
    "BLGA",
    "BLGO",
    "MBLGA",
    "MBLGO",
    "ING",
    "ING.",
    "ABG",
    "ABGA",
    "MED",
    "MED.",
}


def _strip_name_prefixes(value: object) -> str:
    text = str(value or "").replace(".", " ").upper()
    tokens = [token for token in text.split() if token]
    while tokens and tokens[0] in NAME_PREFIXES:
        tokens.pop(0)
    return " ".join(tokens).strip()


def clean_display_name(given_name: object, family_name: object) -> str:
    cleaned_given = _strip_name_prefixes(given_name)
    parts = [cleaned_given, str(family_name or "").strip()]
    return " ".join(part for part in parts if part).strip()


def normalize_match_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.replace(".", " ").replace("-", " ").split())


def uppercase_report_value(value: object) -> str:
    return str(value or "").strip().upper()


def culture_result_code(result: dict) -> str:
    values = result.get("values", []) if isinstance(result, dict) else []
    for parameter in values:
        if parameter.get("code") == "CULTURE_RESULT":
            return uppercase_report_value(parameter.get("value_code") or parameter.get("value_text"))
    return ""


def report_status_label(status: object, culture_result: object = "") -> str:
    status_key = uppercase_report_value(status)
    culture_key = uppercase_report_value(culture_result)
    if status_key == "REJECTED" or culture_key in {"NO_TRAJO_MUESTRA", "MUESTRA_INADECUADA"}:
        return "RECHAZADO"
    if status_key in {"FINAL", "FINAL_VALIDATED"}:
        return "FINALIZADO"
    if status_key == "CANCELLED":
        return "ANULADO"
    return "EN PROCESO"


def report_parameter_method_label(code: object, value: object) -> str:
    code_key = uppercase_report_value(code)
    if code_key == "CULTURE_RESULT":
        return "CULTIVO MANUAL"
    if code_key == "CULTURE_GRAM":
        return "TINCIÓN GRAM"
    if code_key == "CULTURE_NITRITE":
        return "TIRA REACTIVA"
    if code_key == "CULTURE_COLONY_COUNT":
        return "RECUENTO"
    raw = uppercase_report_value(value)
    key = normalize_match_key(raw)
    if not key:
        return "-"
    if key == "cmi" or "microdilucion" in key or "automatizado" in key:
        return "CULTIVO AUTOMATIZADO"
    if key == "disco" or "difusion" in key or "manual" in key:
        return "CULTIVO MANUAL"
    return raw


def editor_ast_method(value: object) -> str:
    return "CMI" if uppercase_report_value(value) == "CMI" else "DISCO"


def report_ast_method_label(value: object) -> str:
    return editor_ast_method(value)


def report_ast_value(method: object, value: object) -> str:
    value_text = str(value or "").strip()
    return value_text if editor_ast_method(method) == "CMI" and value_text else "-"


def render_report_signatures(signer: dict | None) -> str:
    if not signer:
        return ""
    signature_file = signer["file"]
    if not isinstance(signature_file, Path) or not signature_file.exists():
        return ""
    name = html.escape(uppercase_report_value(signer["name"]))
    credential = html.escape(str(signer["credential"]))
    slug = quote(str(signer["slug"]), safe="")
    return f"""
  <section class="signature-panel" aria-label="Firma autorizada">
    <div class="signature-title">Responsable autorizada</div>
    <div class="signature-grid">
    <div class="signature-card">
      <div class="signature-image"><img src="/MUFFIN/firmas/{slug}.jpeg" alt="Sello y firma de {name}"></div>
      <div class="signature-line"></div>
      <strong>{name}</strong>
      <span>{credential}</span>
    </div>
    </div>
  </section>"""


def local_datetime_value(value: object) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
        return parsed.astimezone(LOCAL_TIMEZONE).strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return str(value)[:16]


def select_options_from_schema(options_schema: object) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    if isinstance(options_schema, list):
        raw_options = options_schema
    elif isinstance(options_schema, dict):
        raw_options = options_schema.get("options", options_schema)
    else:
        raw_options = []
    if isinstance(raw_options, list):
        for option in raw_options:
            if isinstance(option, dict):
                code = option.get("code", option.get("value", option.get("id")))
                if code is None:
                    continue
                label = option.get("label", option.get("name", code))
                options.append((str(code), str(label)))
            else:
                text = str(option)
                options.append((text, text))
    elif isinstance(raw_options, dict):
        for code, value in raw_options.items():
            label = value.get("label", value.get("name", code)) if isinstance(value, dict) else value
            options.append((str(code), str(label)))
    return options

CATALOG_FIELD_MAP = {
    "/catalogs/areas": {"id": "area_id", "code": "area_id", "name": "area_desc", "section": "area_seccion", "is_active": "area_estado"},
    "/catalogs/origins": {"id": "procedencia_uuid", "code": "procedencia_id", "name": "procedencia_desc", "is_active": "procedencia_estado"},
    "/catalogs/services": {"id": "servicio_uuid", "code": "servicio_id", "name": "servicio_desc", "is_active": "servicio_estado"},
    "/catalogs/clinicians": {"id": "medico_id", "code": "medico_colegiatura", "given_name": "medico_nombres", "family_name": "medico_apellidos", "is_active": "medico_estado"},
    "/catalogs/exams": {"id": "examen_id", "name": "examen_desc", "external_code": "examen_cod_homo", "barcode_suffix": "examen_codebar_sufijo", "sends_to_analyzer": "examen_analizador_send", "requires_colony_count": "examen_recuento", "is_active": "examen_estado"},
    "/catalogs/organisms": {"id": "orga_id_id", "code": "orga_id", "name": "orga_desc", "homo_code": "orga_homo", "is_active": "orga_estado"},
    "/catalogs/antibiotics": {"id": "atb_id_id", "code": "atb_id", "name": "atb_desc", "homo_code": "atb_homo", "is_active": "atb_estado"},
    "/catalogs/parameters": {"id": "parametro_id", "code": "parametro_cod", "name": "parametro_desc", "section": "parametro_seccion", "is_active": "parametro_estado"},
    "/catalogs/destinations": {"id": "destinos_id", "name": "destinos_desc", "type": "destinos_tipo", "color": "destinos_color", "is_active": "destinos_estado"},
    "/catalogs/containers": {"id": "muestracon_cod", "code": "muestracon_cod", "name": "muestracon_desc", "is_active": "muestracon_estado"},
    "/catalogs/specimen-types": {"id": "muestra_id", "code": "muestra_cod_alfa", "name": "muestra_desc", "container_id": "muestra_contenedor_id", "parent_id": "muestra_padre_id", "is_selectable": "muestra_seleccionable", "is_active": "muestra_estado"},
    "/catalogs/defined-comments": {"id": "rescomen_id", "code": "rescomen_cod", "text": "rescomen_desc", "is_active": "rescomen_estado"},
    "/catalogs/colony-count-options": {"id": "panel_res_recuento_id", "code": "panel_res_recuento_cod", "name": "panel_res_recuento_desc", "is_active": "panel_res_recuento_estado"},
    "/catalogs/ast-panels": {"id": "orga_panel_id", "code": "orga_panel_codigo", "name": "orga_panel_desc", "display_order": "orga_panel_orden", "is_active": "orga_panel_estado"},
}

# SIMCORE frontend field names → MUFFIN API field names for catalog CREATE/UPDATE
CATALOG_CREATE_MAP = {
    "Mic_area/Guardar": ("/catalogs/areas", lambda o: {"code": o.get("area_id", ""), "name": o.get("area_desc", ""), "section": o.get("area_seccion", "MICROBIOLOGY")}),
    "Mic_procedencia/Guardar": ("/catalogs/origins", lambda o: {"code": o.get("procedencia_id", ""), "name": o.get("procedencia_desc", "")}),
    "Mic_servicio/Guardar": ("/catalogs/services", lambda o: {"code": o.get("servicio_id", ""), "name": o.get("servicio_desc", "")}),
    "Mic_medico/Guardar": ("/catalogs/clinicians", lambda o: {"code": o.get("medico_colegiatura", ""), "given_name": o.get("medico_nombres", ""), "family_name": o.get("medico_apellidos", "")}),
    "Mic_examen/Guardar": ("/catalogs/exams", lambda o: {"code": o.get("examen_id", ""), "name": o.get("examen_desc", ""), "external_code": o.get("examen_cod_homo", ""), "barcode_suffix": o.get("examen_codebar_sufijo", ""), "sends_to_analyzer": o.get("examen_analizador_send", False), "requires_colony_count": o.get("examen_recuento", False)}),
    "Mic_muestra/Guardar": ("/catalogs/specimen-types", lambda o: {"code": o.get("muestra_cod_alfa", ""), "name": o.get("muestra_desc", ""), "container_id": o.get("muestra_contenedor_id", "")}),
    "Mic_muestra_contenedor/Guardar": ("/catalogs/containers", lambda o: {"code": o.get("muestracon_cod", ""), "name": o.get("muestracon_desc", "")}),
    "Mic_orga/Guardar": ("/catalogs/organisms", lambda o: {"code": o.get("orga_id", ""), "name": o.get("orga_desc", ""), "homo_code": o.get("orga_homo", "")}),
    "Mic_antibiotico/Guardar": ("/catalogs/antibiotics", lambda o: {"code": o.get("atb_id", ""), "name": o.get("atb_desc", ""), "homo_code": o.get("atb_homo", "")}),
    "Mic_parametro/Guardar": ("/catalogs/parameters", lambda o: {"code": o.get("parametro_cod", ""), "name": o.get("parametro_desc", ""), "section": o.get("parametro_seccion", "MICROBIOLOGY")}),
    "Mic_destinos/Guardar": ("/catalogs/destinations", lambda o: {"name": o.get("destinos_desc", ""), "type": o.get("destinos_tipo", ""), "color": o.get("destinos_color", "")}),
    "Mic_res_comentarios_def/Guardar": ("/catalogs/defined-comments", lambda o: {"code": o.get("rescomen_cod", o.get("coment_id", "")), "text": o.get("rescomen_desc", o.get("coment_desc", ""))}),
    "Mic_res_panel_recuento/Guardar": ("/catalogs/colony-count-options", lambda o: {"code": o.get("panel_res_recuento_cod", o.get("recuento_id", "")), "name": o.get("panel_res_recuento_desc", o.get("recuento_desc", ""))}),
}

API_PROXIES = {
    # ── Dashboard ──
    "Dashboard/Resumen": ("GET", "/dashboard/summary", "dashboard_summary"),
    # ── Users ──
    "Mic_usuario/Obtener": ("GET", "/admin/users", "user_list"),
    "Mic_usuario/Guardar": ("POST", "/admin/users", "user_create"),
    "Mic_usuario/Eliminar": ("POST", "/admin/users", "user_delete"),
    "Mic_usuario/Reactivar": ("POST", "/admin/users", "user_reactivate"),
    "Mic_usuario/Guardar_update_pass": ("POST", "/admin/users", "user_password_update"),
    # ── Catalogs GET ──
    "Mic_area/Obtener": ("GET", "/catalogs/areas", "catalog_list"),
    "Mic_area/Guardar": ("POST", "/catalogs/areas", "catalog_mapped_create"),
    "Mic_procedencia/Obtener": ("GET", "/catalogs/origins", "catalog_list"),
    "Mic_procedencia/Guardar": ("POST", "/catalogs/origins", "catalog_mapped_create"),
    "Mic_servicio/Obtener": ("GET", "/catalogs/services", "catalog_list"),
    "Mic_servicio/Guardar": ("POST", "/catalogs/services", "catalog_mapped_create"),
    "Mic_medico/Obtener": ("GET", "/catalogs/clinicians", "catalog_list"),
    "Mic_medico/Guardar": ("POST", "/catalogs/clinicians", "catalog_mapped_create"),
    "Mic_examen/Obtener": ("GET", "/catalogs/exams", "catalog_list"),
    "Mic_examen/Guardar": ("POST", "/catalogs/exams", "catalog_mapped_create"),
    "Mic_muestra/Obtener": ("GET", "/catalogs/specimen-types", "catalog_list"),
    "Mic_muestra/Guardar": ("POST", "/catalogs/specimen-types", "catalog_mapped_create"),
    "Mic_muestra_contenedor/Obtener": ("GET", "/catalogs/containers", "catalog_list"),
    "Mic_muestra_contenedor/Guardar": ("POST", "/catalogs/containers", "catalog_mapped_create"),
    "Mic_orga/Obtener": ("GET", "/catalogs/organisms", "catalog_list"),
    "Mic_orga/Guardar": ("POST", "/catalogs/organisms", "catalog_mapped_create"),
    "Mic_antibiotico/Obtener": ("GET", "/catalogs/antibiotics", "catalog_list"),
    "Mic_antibiotico/Guardar": ("POST", "/catalogs/antibiotics", "catalog_mapped_create"),
    "Mic_parametro/Obtener": ("GET", "/catalogs/parameters", "catalog_list"),
    "Mic_parametro/Guardar": ("POST", "/catalogs/parameters", "catalog_mapped_create"),
    "Mic_destinos/Obtener": ("GET", "/catalogs/destinations", "catalog_list"),
    "Mic_destinos/Guardar": ("POST", "/catalogs/destinations", "catalog_mapped_create"),
    "Mic_res_comentarios_def/Obtener": ("GET", "/catalogs/defined-comments", "catalog_list"),
    "Mic_res_comentarios_def/Guardar": ("POST", "/catalogs/defined-comments", "catalog_mapped_create"),
    "Mic_res_panel_recuento/Obtener": ("GET", "/catalogs/colony-count-options", "catalog_list"),
    "Mic_res_panel_recuento/Guardar": ("POST", "/catalogs/colony-count-options", "catalog_mapped_create"),
    # ── Legacy sections/configuration ──
    "Mic_seccion/Obtener": ("GET", "/catalogs/areas", "section_list"),
    "Mic_seccion/Guardar": ("POST", "/catalogs/areas", "section_save"),
    "Mic_seccion/ObtenerSecuencia": ("GET", "/catalogs/exams", "section_sequence"),
    "Mic_seccion_examen/Obtener": ("GET", "/catalogs/exams", "section_exam_list"),
    "Mic_seccion_examen/Guardar": ("POST", "/catalogs/exams", "section_exam_save"),
    "Mic_seccion_examen/Eliminar": ("GET", "/catalogs/exams", "section_exam_remove"),
    "Mic_configuracion_general/Obtener": ("GET", "/admin/settings", "general_config_get"),
    "Mic_configuracion_general/Guardar": ("POST", "/admin/settings", "general_config_save"),
    # ── Exam relationships ──
    "Mic_muestra_examen/ObtenerEXA": ("GET", "/catalogs/exams", "exam_specimen_list"),
    "Mic_muestra_examen/Guardar": ("POST", "/catalogs/exams", "exam_specimen_add"),
    "Mic_muestra_examen/Eliminar": ("POST", "/catalogs/exams", "exam_specimen_remove"),
    "Mic_examen_parametro/Obtener": ("GET", "/catalogs/exams", "exam_param_list"),
    "Mic_examen_parametro/Guardar": ("POST", "/catalogs/exams", "exam_param_add"),
    "Mic_examen_parametro/Eliminar": ("POST", "/catalogs/exams", "exam_param_remove"),
    # ── Patients ──
    "Mic_Persona/Obtener": ("GET", "/patients", "patient_list"),
    "Mic_persona/ObtenerHC": ("GET", "/patients", "patient_list"),
    "Mic_Persona/Guardar": ("POST", "/patients", "patient_save"),
    "Mic_Persona/Eliminar": ("POST", "/patients", "patient_delete"),
    # ── Orders ──
    "Mic_orden/Obtener": ("GET", "/orders", "order_list"),
    "Mic_orden/Guardar": ("POST", "/orders", "order_save"),
    "Mic_orden/ObtenerMic_orden_seach_destino": ("GET", "/orders", "destination_order_search"),
    "Mic_orden/RegistrarPrinterCodebar": ("GET", "/print-jobs", "barcode_print"),
    # ── Order items ──
    "Mic_orden_detalle/Obtener_Mic_orden_detalle_examen": ("GET", "/orders", "order_detail_exams"),
    "Mic_orden_detalle/RegistrarExaMuestraMic_orden_detalle": ("POST", "/orders", "order_item_add"),
    "Mic_orden_detalle/EliminarMic_orden_detalle": ("POST", "/orders", "order_item_delete"),
    "Mic_orden_detalle/Obtener_res": ("GET", "/result-worklist", "result_worklist"),
    "Mic_orden_detalle/ObtenerMic_orden_detalle_examen_muestra": ("GET", "/result-worklist", "result_item_sample"),
    "Mic_orden_detalle/GuardarMoMuestra": ("POST", "/orders", "order_item_sample_save"),
    # ── Clinical events ──
    "Mic_orden_detalle/RegistrarEnviarInstrumentoMic_orden_detalle": ("GET", "/orders", "order_item_instrument"),
    "Mic_orden_detalle/RegistrarDeleteEventosMic_orden_detalle": ("POST", "/orders", "order_item_delete_events"),
    "Mic_orden_detalle/RegistrarEnviarAlarmaEmailMic_orden_detalle": ("GET", "/orders", "order_item_email_alarm"),
    # ── Results ──
    "Mic_orden_detalle_res/Guardar": ("POST", "/orders", "result_save"),
    "Mic_orden_detalle_res/ObtenerOrdenId": ("GET", "/orders", "result_get_by_order"),
    "Mic_orden_detalle_res/ObtenerMic_orden_pdf_examen_param": ("GET", "/orders", "legacy_report_params"),
    "Trans_pdf/Download_res_es": ("GET", "/orders", "result_report"),
    "Mic_temp/DocumentoPDF": ("GET", "/orders", "result_report"),
    # ── AST Panels (microbiology) ──
    "Mic_res_panel/Registrar": ("POST", "/orders", "ast_panel_register"),
    "Mic_res_panel/Eliminar": ("GET", "/orders", "ast_panel_delete"),
    "Mic_res_panel/ObtenerCodebar": ("GET", "/orders", "ast_panel_by_codebar"),
    "Mic_res_panel/ObtenerCodebarOrgacod": ("GET", "/orders", "ast_panel_by_org"),
    "Mic_res_panel/ObtenerMic_orden_pdf_panel": ("GET", "/orders", "legacy_report_panels"),
    "Mic_res_panel_detalle/Guardar": ("POST", "/orders", "ast_detail_save"),
    "Mic_res_panel_detalle/GuardarManual": ("POST", "/orders", "ast_detail_manual"),
    "Mic_res_panel_detalle/ObtenerCodebarOrgaCod": ("GET", "/orders", "ast_detail_by_org"),
    "Mic_res_panel_detalle/ObtenerMic_orden_pdf_panel_atb": ("GET", "/orders", "legacy_report_panel_atb"),
    # ── Organism panels ──
    "Mic_orga_panel/Obtener": ("GET", "/catalogs/ast-panels", "catalog_list"),
    "Mic_orga_panel/Guardar": ("POST", "/catalogs/ast-panels", "ast_panel_create"),
    "Mic_orga_panel/Eliminar": ("POST", "/catalogs/ast-panels", "ast_panel_delete"),
    "Mic_orga_panel_detalle/Obtener": ("GET", "/catalogs/ast-panels", "ast_panel_antibiotics"),
    "Mic_orga_panel_detalle/Guardar": ("POST", "/catalogs/ast-panels", "ast_panel_antibiotic_add"),
    "Mic_orga_panel_detalle/Eliminar": ("POST", "/catalogs/ast-panels", "ast_panel_antibiotic_remove"),
    # ── Area permissions (stub — no backend endpoint yet) ──
    "Mic_area_permiso/Obtener": ("GET", "/admin/users", "area_permission_list"),
    "Mic_area_permiso/Obtener_user_seccion": ("GET", "/auth/me/areas", "area_permission_list"),
    "Mic_area_permiso/Guardar": ("POST", "/admin/users", "area_permission_save"),
    "Mic_area_permiso/Eliminar": ("GET", "/admin/users", "area_permission_delete"),
    # ── Verification / consultations / exports ──
    "Mic_destinos_orden_detalle/Obtener": ("GET", "/orders", "destination_order_detail_list"),
    "Mic_destinos_orden_detalle/Guardar": ("POST", "/orders", "destination_order_detail_save"),
    "Mic_destinos_orden_detalle/Verifcar": ("POST", "/orders", "destination_order_verify"),
    "Mic_destinos_orden_detalle/Eliminar": ("GET", "/orders", "destination_order_detail_delete"),
    "Trans_consultas/Obtener_pac_orden": ("GET", "/orders", "consult_patient_orders"),
    "Trans_reportes/Microbiologia_rep_hoja_trabajo_export": ("GET", "/result-worklist", "worksheet_report_export"),
    "Trans_reportes/Microbiologia_rep_idt_ast_export": ("GET", "/result-worklist", "idt_ast_report_export"),
    "Trans_reportes/Microbiologia_rep_produccion_export": ("GET", "/result-worklist", "production_report_export"),
    "Mic_Persona/Exportar": ("GET", "/patients", "patient_export"),
}


def _is_cacheable_api_get(method: str, path: str) -> bool:
    return method == "GET" and path.startswith("/catalogs/")


def _clear_api_cache(prefix: str) -> None:
    stale_keys = [key for key in API_GET_CACHE if key[2].startswith(prefix)]
    for key in stale_keys:
        API_GET_CACHE.pop(key, None)


def api_req(method: str, path: str, token: str = "", body: dict | None = None) -> tuple[int, dict | list | None]:
    if method != "GET" and path.startswith("/catalogs/"):
        _clear_api_cache("/catalogs/")
    cache_key = (API_BASE, token, path)
    if API_CACHE_TTL_SECONDS > 0 and _is_cacheable_api_get(method, path):
        cached = API_GET_CACHE.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1], copy.deepcopy(cached[2])
    try:
        data = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = URLRequest(f"{API_BASE}{path}", data=data, headers=headers, method=method)
        with urlopen(req, timeout=10) as resp:
            content = resp.read()
            payload = json.loads(content.decode("utf-8")) if content else None
            if resp.status == 200 and API_CACHE_TTL_SECONDS > 0 and _is_cacheable_api_get(method, path):
                API_GET_CACHE[cache_key] = (
                    time.monotonic() + API_CACHE_TTL_SECONDS,
                    resp.status,
                    copy.deepcopy(payload),
                )
            return resp.status, payload
    except URLError as e:
        code = e.code if hasattr(e, "code") else 502
        try:
            body_text = e.read().decode("utf-8") if hasattr(e, "read") else ""
            detail = json.loads(body_text).get("detail", "") if body_text else ""
        except Exception:
            detail = ""
        return code, {"detail": detail} if detail else None
    except Exception:
        return 502, None


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"pages": {}}


def content_type(path: Path, request_path: str) -> str:
    lowered = request_path.lower()
    if path.suffix.lower() == ".js" or "/bundles/" in lowered or "/scripts/" in lowered or "/content/pluginsjs" in lowered:
        return "application/javascript; charset=utf-8"
    if path.suffix.lower() == ".css" or "/content/" in lowered:
        return "text/css; charset=utf-8"
    guessed = mimetypes.guess_type(str(path))[0]
    if guessed:
        return guessed
    if path.suffix.lower() in {".html", ".htm"}:
        return "text/html; charset=utf-8"
    return "application/octet-stream"


def is_static_asset(path: Path, request_path: str) -> bool:
    if path.suffix.lower() in {".html", ".htm"}:
        return False
    if request_path in STATIC_CACHEABLE_DIRECT_PATHS or request_path in SIGNATURE_IMAGE_ROUTES:
        return True
    if path.suffix.lower() in STATIC_CACHEABLE_SUFFIXES:
        return True
    return request_path.startswith(STATIC_CACHEABLE_PREFIXES)


def static_cache_control(full_request_path: str) -> str:
    query = urlparse(full_request_path).query
    if "v=" in query:
        return f"public, max-age={STATIC_CACHE_VERSIONED_SECONDS}, immutable"
    return f"public, max-age={STATIC_CACHE_UNVERSIONED_SECONDS}, stale-while-revalidate=604800"


def refresh_frontend_asset_versions(body: bytes) -> bytes:
    replacements = (
        (LEGACY_CSS_VERSIONED_URL, f"/MUFFIN/Content/css.css?v={FRONTEND_ASSET_VERSION}".encode("ascii")),
        (LEGACY_JQUERY_VERSIONED_URL, f"/MUFFIN/bundles/jquery.js?v={FRONTEND_ASSET_VERSION}".encode("ascii")),
        (LEGACY_PLUGIN_JS_VERSIONED_URL, f"/MUFFIN/Content/PluginsJS.js?v={FRONTEND_ASSET_VERSION}".encode("ascii")),
    )
    for old, new in replacements:
        body = body.replace(old, new)
    return body


def safe_mirror_path(request_path: str) -> Path | None:
    rel = STATIC_ASSET_ALIASES.get(request_path, request_path).lstrip("/")
    candidate = (MIRROR / rel).resolve()
    try:
        candidate.relative_to(MIRROR.resolve())
    except ValueError:
        return None
    return candidate


class Handler(BaseHTTPRequestHandler):
    manifest: dict = {}

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def send_bytes(
        self,
        body: bytes,
        status: int,
        ctype: str,
        cache_control: str = "no-store",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        if cache_control == "no-store":
            self.send_header("Pragma", "no-cache")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(body, status, "application/json; charset=utf-8")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if parsed.path.startswith("/api/v1/"):
            self.proxy_api_request(parsed)
            return
        if path == "/MUFFIN/Login/Index":
            self.serve_page("/MUFFIN/Home/Index")
            return
        proxy = self._find_proxy(path, "POST")
        if proxy:
            self._handle_proxy(proxy, path)
            return
        self.stub_response(parsed.path)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/v1/"):
            self.proxy_api_request(parsed)
            return
        proxy = self._find_proxy(parsed.path.rstrip("/"), "PUT")
        if proxy:
            self._handle_proxy(proxy, parsed.path)
            return
        self.stub_response(parsed.path)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/v1/"):
            self.proxy_api_request(parsed)
            return
        proxy = self._find_proxy(parsed.path.rstrip("/"), "DELETE")
        if proxy:
            self._handle_proxy(proxy, parsed.path)
            return
        self.stub_response(parsed.path)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        request_path = unquote(parsed.path)
        if request_path.startswith("/api/v1/"):
            self.proxy_api_request(parsed)
            return
        if request_path in {"/", "/MUFFIN", "/MUFFIN/"}:
            self.serve_page("/MUFFIN/Home/Index")
            return
        if request_path.startswith("/SIMCORE_WEB"):
            redirect_path = request_path.replace("/SIMCORE_WEB", "/MUFFIN", 1)
            self.send_response(301)
            self.send_header("Location", redirect_path)
            self.end_headers()
            return
        if request_path.startswith("/MUFFIN/~/"):
            request_path = request_path.replace("/MUFFIN/~/", "/MUFFIN/", 1)
        if request_path in {"/favicon.ico", "/MUFFIN_FAVICON.png"}:
            self.serve_file(FAVICON, request_path)
            return
        if request_path in {"/MUFFIN_ICONO.jpg", "/MUFFIN/Imagenes/MUFFIN_ICONO.jpg"}:
            self.serve_file(BRAND_IMAGE, request_path)
            return
        if request_path in {"/MUFFIN_PRODUCTO.jpg", "/MUFFIN/Imagenes/MUFFIN_PRODUCTO.jpg"}:
            self.serve_file(PRODUCT_IMAGE, request_path)
            return
        if request_path in {"/MUFFIN_MASCOTA.png", "/MUFFIN/Imagenes/MUFFIN_MASCOTA.png"}:
            self.serve_file(MASCOT_IMAGE, request_path)
            return
        if request_path in SIGNATURE_IMAGE_ROUTES:
            self.serve_file(SIGNATURE_IMAGE_ROUTES[request_path], request_path)
            return
        if request_path.rstrip("/") == "/MUFFIN/Home/Salir":
            self.send_bytes(LOGOUT_REDIRECT, 200, "text/html; charset=utf-8")
            return
        if request_path.rstrip("/") in {"/MUFFIN/Login", "/MUFFIN/Login/Index"}:
            self.serve_file(LOGIN_PAGE, request_path, inject_favicon=True)
            return
        proxy = self._find_proxy(request_path.rstrip("/"), "GET")
        if proxy:
            self._handle_proxy(proxy, request_path)
            return
        if request_path in self.manifest.get("pages", {}):
            self.serve_page(request_path)
            return
        mirror_file = safe_mirror_path(request_path)
        if mirror_file and mirror_file.exists() and mirror_file.is_file():
            self.serve_file(mirror_file, request_path)
            return
        if request_path.startswith("/MUFFIN/"):
            self.stub_response(request_path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Recurso no encontrado")

    def serve_page(self, request_path: str) -> None:
        page_rel = self.manifest.get("pages", {}).get(request_path)
        if not page_rel:
            page_rel = self.manifest.get("pages", {}).get("/MUFFIN/Home/Index")
        if not page_rel:
            self.send_error(HTTPStatus.NOT_FOUND, "Pagina no capturada")
            return
        page_file = (ROOT / page_rel).resolve()
        self.serve_file(page_file, request_path, inject_favicon=True, inject_toggle=True)

    def serve_file(self, path: Path, request_path: str, inject_favicon: bool = False, inject_toggle: bool = False) -> None:
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "Ruta fuera del proyecto")
            return
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Archivo no encontrado")
            return
        cacheable = is_static_asset(path, request_path) and not inject_favicon and not inject_toggle
        cache_control = static_cache_control(self.path) if cacheable else "no-store"
        headers: dict[str, str] = {}
        if cacheable:
            stat = path.stat()
            etag = f'W/"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
            headers["ETag"] = etag
            headers["Last-Modified"] = formatdate(stat.st_mtime, usegmt=True)
            if self.headers.get("If-None-Match") == etag:
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self.send_header("Cache-Control", cache_control)
                self.send_header("ETag", etag)
                self.send_header("Last-Modified", headers["Last-Modified"])
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return
        body = path.read_bytes()
        if path.suffix.lower() in {".html", ".htm"}:
            body = refresh_frontend_asset_versions(body)
            body = apply_runtime_branding(body)
        if inject_favicon:
            closing_head = body.lower().find(b"</head>")
            if closing_head >= 0:
                body = body[:closing_head] + FAVICON_MARKUP + body[closing_head:]
        if inject_toggle:
            body = apply_corporate_footer(body)
            closing_head = body.lower().find(b"</head>")
            if closing_head >= 0:
                body = body[:closing_head] + THEME_TOGGLE_CSS + body[closing_head:]
            closing_body = body.lower().rfind(b"</body>")
            if closing_body >= 0:
                body = body[:closing_body] + THEME_TOGGLE_SCRIPT + body[closing_body:]
        if inject_toggle:
            closing_body = body.lower().rfind(b"</body>")
            if closing_body >= 0:
                body = body[:closing_body] + SESSION_SCRIPT + body[closing_body:]
        if inject_toggle:
            closing_body = body.lower().rfind(b"</body>")
            if closing_body >= 0:
                body = body[:closing_body] + UPPERCASE_SCRIPT + body[closing_body:]
        self.send_bytes(body, 200, content_type(path, request_path), cache_control=cache_control, extra_headers=headers)

    def stub_response(self, request_path: str) -> None:
        lowered = request_path.lower()
        if "download" in lowered or "documentopdf" in lowered or lowered.endswith(".pdf"):
            self.send_bytes(b"PDF no disponible en modo frontend local.", 200, "text/plain; charset=utf-8")
            return
        if any(word in lowered for word in ["guardar", "registrar", "eliminar", "actualizar"]):
            self.send_json({"resultado": False, "mensaje": "Esta funcionalidad no esta conectada al backend MUFFIN."})
            return
        self.send_json({"data": [], "recordsTotal": 0, "recordsFiltered": 0, "resultado": True, "mensaje": "Modo local: endpoint sin datos."})

    # ── API proxy ──

    def proxy_api_request(self, parsed) -> None:
        api_path = parsed.path[len("/api/v1"):] or "/"
        target = f"{API_BASE}{api_path}"
        if parsed.query:
            target = f"{target}?{parsed.query}"
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else None
        headers = {"Content-Type": self.headers.get("Content-Type", "application/json")}
        authorization = self.headers.get("Authorization")
        if authorization:
            headers["Authorization"] = authorization
        try:
            request = URLRequest(target, data=body, headers=headers, method=self.command)
            with urlopen(request, timeout=30) as response:
                response_body = response.read()
                self.send_bytes(
                    response_body,
                    response.status,
                    response.headers.get("Content-Type", "application/json; charset=utf-8"),
                )
        except URLError as error:
            status = error.code if hasattr(error, "code") else 502
            response_body = error.read() if hasattr(error, "read") else b""
            self.send_bytes(
                response_body or b'{"detail":"Backend MUFFIN no disponible"}',
                status,
                getattr(error, "headers", {}).get("Content-Type", "application/json; charset=utf-8"),
            )

    def _find_proxy(self, path: str, method: str) -> tuple | None:
        if not path.startswith("/MUFFIN/"):
            return None
        simcore_endpoint = path[len("/MUFFIN/"):]
        simcore_endpoint_key = simcore_endpoint.casefold()
        for api_path, (api_method, api_url, handler) in API_PROXIES.items():
            if simcore_endpoint_key == api_path.casefold() and api_method == method:
                return (api_method, api_url, handler)
        return None

    def _handle_proxy(self, proxy: tuple, path: str) -> None:
        api_method, api_url, handler = proxy
        authorization = self.headers.get("Authorization", "")
        token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
        if not token:
            self.send_json({"resultado": False, "mensaje": "Sesion MUFFIN requerida."}, 401)
            return

        dispatch = {
            "user_list": lambda: self._proxy_user_list(token),
            "user_create": lambda: self._proxy_user_create(token),
            "user_delete": lambda: self._proxy_user_delete(token),
            "user_reactivate": lambda: self._proxy_user_reactivate(token),
            "user_password_update": lambda: self._proxy_user_password_update(token),
            "dashboard_summary": lambda: self._proxy_dashboard_summary(token),
            "catalog_list": lambda: self._proxy_catalog_list(token, api_url),
            "catalog_mapped_create": lambda: self._proxy_catalog_mapped_create(token, api_url),
            "section_list": lambda: self._proxy_section_list(token),
            "section_save": lambda: self._proxy_section_save(token),
            "section_sequence": lambda: self._proxy_section_sequence(token, path),
            "section_exam_list": lambda: self._proxy_section_exam_list(token, path),
            "section_exam_save": lambda: self._proxy_section_exam_save(token),
            "section_exam_remove": lambda: self._proxy_section_exam_remove(token),
            "general_config_get": lambda: self._proxy_general_config_get(token),
            "general_config_save": lambda: self._proxy_general_config_save(token),
            "area_permission_list": lambda: self._proxy_area_permission_list(token),
            "area_permission_save": lambda: self._proxy_area_permission_save(token),
            "area_permission_delete": lambda: self._proxy_area_permission_delete(token),
            "exam_specimen_list": lambda: self._proxy_exam_specimen_list(token, path),
            "exam_specimen_add": lambda: self._proxy_exam_specimen_add(token, path),
            "exam_specimen_remove": lambda: self._proxy_exam_specimen_remove(token, path),
            "exam_param_list": lambda: self._proxy_exam_param_list(token, path),
            "exam_param_add": lambda: self._proxy_exam_param_add(token, path),
            "exam_param_remove": lambda: self._proxy_exam_param_remove(token, path),
            "patient_list": lambda: self._proxy_patient_list(token),
            "patient_save": lambda: self._proxy_patient_save(token),
            "patient_delete": lambda: self._proxy_patient_delete(token),
            "order_list": lambda: self._proxy_order_list(token),
            "order_save": lambda: self._proxy_order_save(token),
            "destination_order_search": lambda: self._proxy_destination_order_search(token, path),
            "barcode_print": lambda: self._proxy_barcode_print(token, path),
            "order_detail_exams": lambda: self._proxy_order_detail_exams(token, path),
            "order_item_add": lambda: self._proxy_order_item_add(token),
            "order_item_delete": lambda: self._proxy_order_item_delete(token),
            "order_item_results": lambda: self._proxy_order_item_results(token, path),
            "result_worklist": lambda: self._proxy_result_worklist(token),
            "result_item_sample": lambda: self._proxy_result_item_sample(token),
            "order_item_sample_save": lambda: self._proxy_order_item_sample_save(token),
            "order_item_instrument": lambda: self._proxy_disabled("Interfaz con instrumento deshabilitada temporalmente"),
            "order_item_delete_events": lambda: self._proxy_result_delete(token),
            "order_item_email_alarm": lambda: self._proxy_disabled("Envio de alarmas por email deshabilitado temporalmente"),
            "result_save": lambda: self._proxy_result_save(token),
            "result_get_by_order": lambda: self._proxy_result_get_by_order(token, path),
            "legacy_report_params": lambda: self._proxy_legacy_report_params(token, path),
            "result_report": lambda: self._proxy_result_report(token, path),
            "ast_panel_register": lambda: self._proxy_ast_panel_register(token),
            "ast_panel_delete": lambda: self._proxy_ast_panel_delete(token),
            "ast_panel_by_codebar": lambda: self._proxy_ast_panel_by_codebar(token, path),
            "ast_panel_by_org": lambda: self._proxy_ast_panel_by_org(token, path),
            "legacy_report_panels": lambda: self._proxy_legacy_report_panels(token, path),
            "ast_detail_save": lambda: self._proxy_ast_detail_save(token),
            "ast_detail_manual": lambda: self._proxy_ast_detail_manual(token),
            "ast_detail_by_org": lambda: self._proxy_ast_detail_by_org(token, path),
            "legacy_report_panel_atb": lambda: self._proxy_legacy_report_panel_atb(token, path),
            "ast_panel_create": lambda: self._proxy_ast_panel_create(token),
            "ast_panel_delete_api": lambda: self._proxy_ast_panel_delete_api(token, path),
            "ast_panel_antibiotics": lambda: self._proxy_ast_panel_antibiotics(token, path),
            "ast_panel_antibiotic_add": lambda: self._proxy_ast_panel_antibiotic_add(token),
            "ast_panel_antibiotic_remove": lambda: self._proxy_ast_panel_antibiotic_remove(token, path),
            "destination_order_detail_list": lambda: self._proxy_destination_order_detail_list(token, path),
            "destination_order_detail_save": lambda: self._proxy_destination_order_detail_save(token),
            "destination_order_verify": lambda: self._proxy_destination_order_verify(token),
            "destination_order_detail_delete": lambda: self._proxy_destination_order_detail_delete(token),
            "consult_patient_orders": lambda: self._proxy_consult_patient_orders(token),
            "worksheet_report_export": lambda: self._proxy_worksheet_report_export(token, path),
            "idt_ast_report_export": lambda: self._proxy_idt_ast_report_export(token, path),
            "production_report_export": lambda: self._proxy_production_report_export(token, path),
            "patient_export": lambda: self._proxy_patient_export(token),
        }

        fn = dispatch.get(handler)
        if fn:
            fn()
        else:
            self.stub_response(path)

    def _read_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            try:
                raw = self.rfile.read(length)
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, Exception):
                return None
        return None

    def _api_error(self, status: int, data) -> str:
        if isinstance(data, dict):
            return data.get("detail", "")
        return ""

    def _proxy_stub_ok(self, msg: str) -> None:
        self.send_json({"resultado": True, "mensaje": msg})

    def _proxy_disabled(self, msg: str) -> None:
        self.send_json({"resultado": False, "mensaje": msg}, 409)

    # ── DASHBOARD HANDLERS ──

    def _proxy_dashboard_summary(self, token: str) -> None:
        today = datetime.now(LOCAL_TIMEZONE).date()
        week_start = today - timedelta(days=6)

        def load_worklist(start: date, end: date) -> list[dict]:
            status, data = api_req("GET", f"/result-worklist?from={start.isoformat()}&to={end.isoformat()}", token)
            return data if status == 200 and isinstance(data, list) else []

        def load_order_count(start: date, end: date) -> int:
            status, data = api_req("GET", f"/orders?from={start.isoformat()}&to={end.isoformat()}&page_size=100", token)
            if status == 200 and isinstance(data, dict):
                return int(data.get("total", len(data.get("data", [])) or 0))
            if status == 200 and isinstance(data, list):
                return len(data)
            return 0

        def item_status(row: dict) -> str:
            item = row.get("item") or {}
            result = row.get("result") or {}
            return str(result.get("status") or item.get("status") or "SIN_RESULTADO")

        def summarize(rows: list[dict]) -> dict[str, int]:
            final = sum(1 for row in rows if item_status(row) == "FINAL_VALIDATED")
            preliminary = sum(1 for row in rows if item_status(row) == "PRELIMINARY_VALIDATED")
            saved = sum(1 for row in rows if item_status(row) in {"RESULT_SAVED", "IN_PROCESS"})
            received = sum(1 for row in rows if item_status(row) in {"REGISTERED", "COLLECTED", "RECEIVED", "SIN_RESULTADO"})
            pending = max(len(rows) - final, 0)
            return {
                "total": len(rows),
                "pendientes": pending,
                "recibidos": received,
                "en_proceso": saved,
                "preliminares": preliminary,
                "finalizados": final,
            }

        today_rows = load_worklist(today, today)
        week_rows = load_worklist(week_start, today)
        today_summary = summarize(today_rows)
        week_summary = summarize(week_rows)
        today_summary["ordenes"] = load_order_count(today, today)
        week_summary["ordenes"] = load_order_count(week_start, today)
        week_summary["porcentaje_finalizado"] = round((week_summary["finalizados"] / week_summary["total"]) * 100) if week_summary["total"] else 0

        self.send_json(
            {
                "resultado": True,
                "fecha": today.isoformat(),
                "rango_7_dias": {"desde": week_start.isoformat(), "hasta": today.isoformat()},
                "hoy": today_summary,
                "ultimos_7_dias": week_summary,
                "actualizado": datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # ── USER HANDLERS ──

    def _proxy_user_list(self, token: str) -> None:
        status, data = api_req("GET", "/admin/users", token)
        if status == 200 and isinstance(data, list):
            translated = [{"usuario_id": u.get("username", ""), "usuario_apellidos": u.get("family_name", ""), "usuario_nombres": u.get("given_name", ""), "usuario_estado": u.get("is_active", True), "usuario_rol": ROLE_REV.get((u.get("roles") or [None])[0], 4), "usuario_cod_homo": ""} for u in data]
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_user_delete(self, token: str) -> None:
        body = self._read_body()
        username = (body or {}).get("usuario_id", "") or (body or {}).get("username", "")
        if not username:
            self.send_json({"resultado": False, "mensaje": "usuario_id requerido"})
            return
        status, data = api_req("GET", "/admin/users", token)
        user = next((u for u in (data or []) if u.get("username") == username), None) if status == 200 and isinstance(data, list) else None
        if not user:
            self.send_json({"resultado": False, "mensaje": "Usuario no encontrado"})
            return
        if not user.get("is_active", True):
            self.send_json({"resultado": False, "mensaje": "El usuario ya esta inactivo"})
            return
        del_status, del_data = api_req("DELETE", f"/admin/users/{user['id']}", token)
        if del_status in (200, 204):
            self.send_json({"resultado": True, "mensaje": f"Usuario {username} desactivado correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(del_status, del_data) or f"No se pudo desactivar (HTTP {del_status})"})

    def _proxy_user_reactivate(self, token: str) -> None:
        body = self._read_body()
        username = (body or {}).get("usuario_id", "") or (body or {}).get("username", "")
        if not username:
            self.send_json({"resultado": False, "mensaje": "usuario_id requerido"})
            return
        status, data = api_req("GET", "/admin/users", token)
        user = next((u for u in (data or []) if u.get("username") == username), None) if status == 200 and isinstance(data, list) else None
        if not user:
            self.send_json({"resultado": False, "mensaje": "Usuario no encontrado"})
            return
        if user.get("is_active", True):
            self.send_json({"resultado": False, "mensaje": "El usuario ya esta activo"})
            return
        re_status, re_data = api_req("POST", f"/admin/users/{user['id']}/reactivate", token)
        if re_status in (200, 201):
            self.send_json({"resultado": True, "mensaje": f"Usuario {username} reactivado correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(re_status, re_data) or f"No se pudo reactivar (HTTP {re_status})"})

    def _proxy_user_create(self, token: str) -> None:
        body = self._read_body()
        if not body or "objeto" not in body:
            self.send_json({"resultado": False, "mensaje": "Datos invalidos"})
            return
        obj = body["objeto"]
        rid = obj.get("usuario_rol", 4)
        if isinstance(rid, str):
            rid = int(rid) if rid.isdigit() else 4
        role_code = ROLE_MAP.get(rid, "ENTRY")
        username = obj.get("usuario_id", "")
        password = obj.get("usuario_pass", "")
        if not username:
            self.send_json({"resultado": False, "mensaje": "El usuario es obligatorio"})
            return
        status, existing_list = api_req("GET", "/admin/users", token)
        existing = next((u for u in (existing_list or []) if u.get("username") == username), None) if status == 200 and isinstance(existing_list, list) else None
        if existing:
            update_payload = {"given_name": obj.get("usuario_nombres", existing.get("given_name", "")), "family_name": obj.get("usuario_apellidos", existing.get("family_name", "")), "role_codes": [role_code]}
            if password:
                if len(password) < 8:
                    self.send_json({"resultado": False, "mensaje": "La contraseña debe tener al menos 8 caracteres"})
                    return
                update_payload["password"] = password
            if "usuario_estado" in obj:
                update_payload["is_active"] = obj["usuario_estado"]
            put_status, put_data = api_req("PUT", f"/admin/users/{existing['id']}", token, update_payload)
            if put_status == 200:
                self.send_json({"resultado": True, "mensaje": "Usuario actualizado correctamente"})
            else:
                self.send_json({"resultado": False, "mensaje": self._api_error(put_status, put_data) or f"Error al actualizar (HTTP {put_status})"})
            return
        if len(password) < 8:
            self.send_json({"resultado": False, "mensaje": "La contraseña es obligatoria y debe tener al menos 8 caracteres"})
            return
        payload = {"username": username, "given_name": obj.get("usuario_nombres", ""), "family_name": obj.get("usuario_apellidos", ""), "password": password, "role_codes": [role_code], "area_permissions": []}
        create_status, create_data = api_req("POST", "/admin/users", token, payload)
        if create_status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Usuario creado correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(create_status, create_data) or f"Error al crear usuario (HTTP {create_status})"})

    def _proxy_user_password_update(self, token: str) -> None:
        body = self._read_body()
        username = ""
        new_password = ""
        if body:
            username = body.get("usuario_id", "") or body.get("username", "")
            if "objeto" in body:
                obj = body["objeto"]
                username = username or obj.get("usuario_id", "")
                new_password = obj.get("usuario_pass", "")
        if not username:
            self.send_json({"resultado": False, "mensaje": "usuario_id requerido"})
            return
        if not new_password:
            self.send_json({"resultado": False, "mensaje": "Nueva contrasena requerida"})
            return
        status, data = api_req("GET", "/admin/users", token)
        user = next((u for u in (data or []) if u.get("username") == username), None) if status == 200 and isinstance(data, list) else None
        if not user:
            self.send_json({"resultado": False, "mensaje": "Usuario no encontrado"})
            return
        put_status, put_data = api_req("PUT", f"/admin/users/{user['id']}", token, {"password": new_password})
        if put_status == 200:
            self.send_json({"resultado": True, "mensaje": "Contrasena actualizada correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(put_status, put_data) or f"Error (HTTP {put_status})"})

    # ── CATALOG HANDLERS ──

    def _proxy_catalog_list(self, token: str, api_url: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        search = self._extract_query_param(request_path, "search")
        page_size = self._extract_query_param(request_path, "page_size")
        if not page_size:
            page_size = "3000" if api_url == "/catalogs/organisms" else "100"
        query = [f"page_size={page_size}"]
        active_only = self._extract_query_param(request_path, "active_only")
        if active_only:
            query.append(f"active_only={quote(active_only, safe='')}")
        if search:
            query.append(f"search={quote(search, safe='')}")
        status, data = api_req("GET", f"{api_url}?{'&'.join(query)}", token)
        items = []
        if status == 200 and isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif status == 200 and isinstance(data, list):
            items = data
        if api_url == "/catalogs/organisms":
            items = sorted(items, key=lambda item: normalize_match_key(item.get("name")))
        elif api_url == "/catalogs/colony-count-options":
            items = sorted(items, key=lambda item: item.get("code", ""))
        mapping = CATALOG_FIELD_MAP.get(api_url)
        if mapping and items:
            translated = [{dst: i.get(src, "") for src, dst in mapping.items()} for i in items]
            self.send_json({"data": translated, "resultado": True})
        elif items:
            self.send_json({"data": items, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_catalog_mapped_create(self, token: str, api_url: str) -> None:
        body = self._read_body()
        if not body:
            self.send_json({"resultado": False, "mensaje": "Datos invalidos"})
            return
        obj = body.get("objeto", body)
        # Find matching create map entry
        path_suffix = api_url.lstrip("/")
        for key, (url, mapper) in CATALOG_CREATE_MAP.items():
            if url.lstrip("/") == path_suffix:
                payload = mapper(obj)
                if not payload.get("code") and not payload.get("name"):
                    self.send_json({"resultado": False, "mensaje": "Codigo y nombre requeridos"})
                    return
                status, data = api_req("POST", url, token, payload)
                if status in (200, 201):
                    self.send_json({"resultado": True, "mensaje": "Guardado correctamente"})
                else:
                    self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})
                return
        # Fallback: generic create
        payload = {"code": obj.get("code", obj.get("id", "")), "name": obj.get("name", obj.get("desc", ""))}
        if not payload.get("code"):
            self.send_json({"resultado": False, "mensaje": "Codigo requerido"})
            return
        status, data = api_req("POST", api_url, token, payload)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Guardado correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    # ── AREA PERMISSIONS (stubs) ──

    def _proxy_area_permission_list(self, token: str) -> None:
        status, data = api_req("GET", "/auth/me/areas", token)
        if status == 200 and isinstance(data, list):
            translated = [
                {
                    "oMic_area": {
                        "area_id": area.get("id", ""),
                        "area_codigo": area.get("code", ""),
                        "area_desc": area.get("name", ""),
                        "area_seccion": area.get("section", ""),
                    },
                    "permiso_validacion_preliminar": area.get("can_preliminary_validate", False),
                    "permiso_validacion_final": area.get("can_final_validate", False),
                }
                for area in data
            ]
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudieron cargar las areas autorizadas"})

    def _proxy_area_permission_save(self, token: str) -> None:
        self.send_json({"resultado": False, "mensaje": "Permisos de area: funcionalidad pendiente de implementar en la API MUFFIN"})

    def _proxy_area_permission_delete(self, token: str) -> None:
        self.send_json({"resultado": False, "mensaje": "Permisos de area: funcionalidad pendiente de implementar en la API MUFFIN"})

    # ── EXAM RELATIONSHIPS ──

    def _proxy_exam_specimen_list(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        exam_id = (
            self._extract_query_param(request_path, "EXA")
            or self._extract_query_param(request_path, "examen_id")
            or self._extract_query_param(request_path, "exam_id")
        )
        if not exam_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/catalogs/exams/{exam_id}/specimen-types", token)
        if status == 200 and isinstance(data, list):
            specimen_status, specimen_page = api_req("GET", "/catalogs/specimen-types?page_size=100", token)
            if specimen_status != 200 or not isinstance(specimen_page, dict):
                self.send_json({"data": [], "resultado": False, "mensaje": "No se pudo cargar la jerarquia de muestras"})
                return
            linked_ids = {relation.get("specimen_type_id") for relation in data}
            translated = [
                {
                    "oMic_muestra": {
                        "muestra_id": specimen.get("id", ""),
                        "muestra_cod_alfa": specimen.get("code", ""),
                        "muestra_desc": specimen.get("name", ""),
                        "muestra_padre_id": specimen.get("parent_id"),
                        "muestra_seleccionable": specimen.get("is_selectable", True),
                    }
                }
                for specimen in specimen_page.get("data", [])
                if specimen.get("id") in linked_ids
            ]
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_exam_specimen_add(self, token: str, path: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        exam_id = obj.get("examen_id", "")
        specimen_id = obj.get("muestra_id", "")
        if not exam_id or not specimen_id:
            self.send_json({"resultado": False, "mensaje": "examen_id y muestra_id requeridos"})
            return
        status, data = api_req("PUT", f"/catalogs/exams/{exam_id}/specimen-types/{specimen_id}", token, {})
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Relacion examen-muestra guardada"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_exam_specimen_remove(self, token: str, path: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        exam_id = obj.get("examen_id", "")
        specimen_id = obj.get("muestra_id", "")
        if not exam_id or not specimen_id:
            self.send_json({"resultado": False, "mensaje": "examen_id y muestra_id requeridos"})
            return
        status, data = api_req("DELETE", f"/catalogs/exams/{exam_id}/specimen-types/{specimen_id}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Relacion eliminada"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_exam_param_list(self, token: str, path: str) -> None:
        exam_id = self._extract_query_param(path, "examen_id") or self._extract_query_param(path, "exam_id")
        if not exam_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/catalogs/exams/{exam_id}/parameters", token)
        if status == 200 and isinstance(data, list):
            translated = [{"exaparam_id": p.get("id", ""), "parametro_cod": p.get("code", ""), "parametro_desc": p.get("name", ""), "exaparam_orden": p.get("sort_order", 0)} for p in data]
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_exam_param_add(self, token: str, path: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        exam_id = obj.get("examen_id", "")
        param_id = obj.get("parametro_id", "")
        if not exam_id or not param_id:
            self.send_json({"resultado": False, "mensaje": "examen_id y parametro_id requeridos"})
            return
        status, data = api_req("PUT", f"/catalogs/exams/{exam_id}/parameters/{param_id}", token, {"sort_order": obj.get("exaparam_orden", 0)})
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Relacion examen-parametro guardada"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_exam_param_remove(self, token: str, path: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        exam_id = obj.get("examen_id", "")
        param_id = obj.get("parametro_id", "")
        if not exam_id or not param_id:
            self.send_json({"resultado": False, "mensaje": "examen_id y parametro_id requeridos"})
            return
        status, data = api_req("DELETE", f"/catalogs/exams/{exam_id}/parameters/{param_id}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Relacion eliminada"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    # ── LEGACY SECTION / CONFIGURATION HANDLERS ──

    def _legacy_section_row(self, area: dict, index: int = 1) -> dict:
        code = str(area.get("code", "")).upper()
        return {
            "seccion_id": area.get("id", ""),
            "seccion_nombre": area.get("name", ""),
            "seccion_nomenplatura": code,
            "seccion_codigo": code,
            "seccion_anio": str(datetime.now(LOCAL_TIMEZONE).year),
            "seccion_numero": index,
            "seccion_estado": area.get("is_active", True),
        }

    def _proxy_section_list(self, token: str) -> None:
        status, data = api_req("GET", "/catalogs/areas?active_only=false&page_size=100", token)
        if status == 200 and isinstance(data, dict):
            rows = [self._legacy_section_row(area, i + 1) for i, area in enumerate(data.get("data", []))]
            self.send_json({"data": rows, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudieron cargar las secciones"})

    def _proxy_section_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        area_id = str(obj.get("seccion_id", "")).strip()
        code = str(obj.get("seccion_codigo") or obj.get("seccion_nomenplatura") or obj.get("seccion_nombre") or "").strip().upper().replace(" ", "_")
        name = str(obj.get("seccion_nombre", "")).strip().upper()
        if not code or not name:
            self.send_json({"resultado": False, "mensaje": "Codigo y nombre de seccion requeridos"})
            return
        payload = {"code": code, "name": name, "section": "MICROBIOLOGY", "is_active": True}
        if area_id and area_id != "0":
            status, data = api_req("PATCH", f"/catalogs/areas/{quote(area_id, safe='')}", token, payload)
        else:
            status, data = api_req("POST", "/catalogs/areas", token, payload)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Seccion guardada correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo guardar la seccion (HTTP {status})"})

    def _proxy_section_sequence(self, token: str, path: str) -> None:
        exam_id = self._extract_query_param(path, "examen_id")
        if not exam_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, exam_page = api_req("GET", "/catalogs/exams?active_only=false&page_size=100", token)
        area_id = ""
        if status == 200 and isinstance(exam_page, dict):
            for exam in exam_page.get("data", []):
                if str(exam.get("id", "")) == exam_id or str(exam.get("code", "")) == exam_id:
                    area_id = exam.get("laboratory_area_id", "")
                    break
        area_row = {}
        if area_id:
            area_status, area_page = api_req("GET", "/catalogs/areas?active_only=false&page_size=100", token)
            if area_status == 200 and isinstance(area_page, dict):
                area_row = next((area for area in area_page.get("data", []) if area.get("id") == area_id), {})
        self.send_json({"data": [self._legacy_section_row(area_row or {"code": "", "name": ""})], "resultado": True})

    def _proxy_section_exam_list(self, token: str, path: str) -> None:
        section_id = self._extract_query_param(path, "seccion_id")
        status, data = api_req("GET", "/catalogs/exams?active_only=false&page_size=100", token)
        if status == 200 and isinstance(data, dict):
            rows = []
            for exam in data.get("data", []):
                if not section_id or exam.get("laboratory_area_id") == section_id:
                    rows.append(
                        {
                            "secciondet_id": f"{section_id}:{exam.get('id', '')}",
                            "seccion_id": section_id,
                            "examen_id": exam.get("id", ""),
                            "examen_desc": exam.get("name", ""),
                        }
                    )
            self.send_json({"data": rows, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudieron cargar los examenes de la seccion"})

    def _proxy_section_exam_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        section_id = str(obj.get("seccion_id", "")).strip()
        exam_id = str(obj.get("examen_id", "")).strip()
        if not section_id or not exam_id:
            self.send_json({"resultado": False, "mensaje": "Seccion y examen requeridos"})
            return
        status, data = api_req("PATCH", f"/catalogs/exams/{quote(exam_id, safe='')}", token, {"laboratory_area_id": section_id})
        if status == 200:
            self.send_json({"resultado": True, "mensaje": "Examen asociado a la seccion"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo asociar examen (HTTP {status})"})

    def _proxy_section_exam_remove(self, token: str) -> None:
        self.send_json({"resultado": False, "mensaje": "Un examen no puede quedar sin seccion. Asocielo a otra seccion para corregirlo."}, 409)

    def _general_config_default(self) -> dict:
        return {
            "confi_centro_cod": "HSRA",
            "confi_centro_desc": INSTITUTION_NAME,
            "confi_impresora_nombre": "",
            "confi_impresora_cantidad": "1",
            "confi_impresora_etiqueta_adicional": False,
            "confi_reporte_muestra_toma": True,
            "confi_reporte_muestra_recepcion": True,
            "confi_reporte_codebar": True,
            "confi_analizador_lista_trabajo": "",
        }

    def _proxy_general_config_get(self, token: str) -> None:
        status, data = api_req("GET", "/admin/settings", token)
        value = self._general_config_default()
        if status == 200 and isinstance(data, list):
            saved = next((item.get("value") for item in data if item.get("key") == "general"), None)
            if isinstance(saved, dict):
                value.update(saved)
        self.send_json({"data": [value], "resultado": True})

    def _proxy_general_config_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        value = self._general_config_default()
        value.update(
            {
                "confi_centro_cod": str(obj.get("confi_centro_cod", "")).strip().upper(),
                "confi_centro_desc": str(obj.get("confi_centro_desc", "")).strip(),
                "confi_impresora_nombre": str(obj.get("confi_impresora_nombre", "")).strip(),
                "confi_impresora_cantidad": str(obj.get("confi_impresora_cantidad", "1")).strip() or "1",
                "confi_impresora_etiqueta_adicional": bool(obj.get("confi_impresora_etiqueta_adicional")),
                "confi_reporte_muestra_toma": bool(obj.get("confi_reporte_muestra_toma")),
                "confi_reporte_muestra_recepcion": bool(obj.get("confi_reporte_muestra_recepcion")),
                "confi_reporte_codebar": bool(obj.get("confi_reporte_codebar")),
                "confi_analizador_lista_trabajo": str(obj.get("confi_analizador_lista_trabajo", "")).strip(),
            }
        )
        if not value["confi_centro_cod"] or not value["confi_centro_desc"]:
            self.send_json({"resultado": False, "mensaje": "Codigo y descripcion del centro requeridos"})
            return
        status, data = api_req("PUT", "/admin/settings/general", token, {"value": value})
        if status == 200:
            self.send_json({"resultado": True, "mensaje": "Configuracion guardada correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo guardar configuracion (HTTP {status})"})

    # ── PATIENT HANDLERS ──

    def _proxy_patient_list(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        hc = (
            self._extract_query_param(request_path, "HC")
            or self._extract_query_param(request_path, "hc")
            or self._extract_query_param(request_path, "historia_clinica")
        )
        if hc:
            status, data = api_req("GET", f"/patients?search={quote(hc, safe='')}&page_size=100", token)
        else:
            status, data = api_req("GET", "/patients?page_size=100", token)
        items = []
        if status == 200 and isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif status == 200 and isinstance(data, list):
            items = data
        translated = []
        for patient in items:
            birth_date = patient.get("birth_date", "")
            age = ""
            if birth_date:
                try:
                    born = date.fromisoformat(birth_date)
                    today = date.today()
                    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                except ValueError:
                    pass
            translated.append(
                {
                    "persona_id": patient.get("id", ""),
                    "persona_hc": patient.get("medical_record_number", ""),
                    "persona_apellidos": patient.get("family_name", ""),
                    "persona_nombres": patient.get("given_name", ""),
                    "persona_genero": patient.get("sex", ""),
                    "persona_fecha_nac": birth_date,
                    "persona_edad": age,
                }
            )
        self.send_json({"data": translated, "resultado": True})

    def _proxy_patient_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        hc = str(obj.get("persona_hc", "")).strip().upper()
        if not hc:
            self.send_json({"resultado": False, "mensaje": "Historia clinica requerida"})
            return
        payload = {
            "medical_record_number": hc,
            "family_name": str(obj.get("persona_apellidos", "")).strip().upper(),
            "given_name": str(obj.get("persona_nombres", "")).strip().upper(),
            "birth_date": obj.get("persona_fecha_nac") or None,
            "sex": str(obj.get("persona_genero", "")).strip().upper(),
        }
        patient_id = str(obj.get("persona_id", "")).strip()
        if patient_id and patient_id != "0":
            status, data = api_req("PATCH", f"/patients/{patient_id}", token, payload)
        else:
            status, data = api_req("POST", "/patients", token, payload)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Paciente guardado correctamente"})
        elif status == 409:
            self.send_json({"resultado": False, "mensaje": "El numero de HC ya esta registrado"})
        elif status == 422:
            self.send_json({"resultado": False, "mensaje": "Revise HC, apellidos, nombres, fecha de nacimiento y genero"})
        elif status == 403:
            self.send_json({"resultado": False, "mensaje": "Su usuario no tiene permiso para guardar pacientes"})
        else:
            self.send_json({"resultado": False, "mensaje": f"No se pudo guardar el paciente (HTTP {status})"})

    def _proxy_patient_delete(self, token: str) -> None:
        body = self._read_body()
        request_path = self.path if hasattr(self, "path") else ""
        obj = (body or {}).get("objeto", body or {})
        patient_id = (
            str(obj.get("persona_id", "")).strip()
            or self._extract_query_param(request_path, "persona_id")
            or self._extract_query_param(request_path, "patient_id")
        )
        if not patient_id:
            self.send_json({"resultado": False, "mensaje": "Paciente requerido"})
            return
        status, data = api_req("DELETE", f"/patients/{quote(patient_id, safe='')}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Paciente eliminado correctamente"})
        elif status == 409:
            self.send_json(
                {
                    "resultado": False,
                    "mensaje": "No se puede eliminar: el paciente tiene resultados finales validados",
                }
            )
        elif status == 403:
            self.send_json({"resultado": False, "mensaje": "Su usuario no tiene permiso para eliminar pacientes"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo eliminar el paciente (HTTP {status})"})

    # ── ORDER HANDLERS ──

    def _proxy_order_list(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        date_from = self._extract_query_param(request_path, "orden_fecha_ini")
        date_to = self._extract_query_param(request_path, "orden_fecha_fin")
        search = self._extract_query_param(request_path, "orden_buscar")
        query = ["page_size=100"]
        if date_from:
            query.append(f"from={quote(date_from, safe='')}")
        if date_to:
            query.append(f"to={quote(date_to, safe='')}")
        if search:
            query.append(f"search={quote(search, safe='')}")
        status, data = api_req("GET", f"/orders?{'&'.join(query)}", token)
        items = []
        if status == 200 and isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif status == 200 and isinstance(data, list):
            items = data
        _, patient_page = api_req("GET", "/patients?page_size=100", token)
        _, origin_page = api_req("GET", "/catalogs/origins?page_size=100", token)
        _, service_page = api_req("GET", "/catalogs/services?page_size=100", token)
        _, clinician_page = api_req("GET", "/catalogs/clinicians?page_size=100", token)
        patients = {item["id"]: item for item in (patient_page or {}).get("data", [])}
        origins = {item["id"]: item for item in (origin_page or {}).get("data", [])}
        services = {item["id"]: item for item in (service_page or {}).get("data", [])}
        clinicians = {item["id"]: item for item in (clinician_page or {}).get("data", [])}
        translated = []
        for order in items:
            patient = patients.get(order.get("patient_id"), {})
            origin = origins.get(order.get("origin_id"), {})
            service = services.get(order.get("service_id"), {})
            clinician = clinicians.get(order.get("clinician_id"), {})
            birth_date = patient.get("birth_date", "")
            age = ""
            if birth_date:
                try:
                    born = date.fromisoformat(birth_date)
                    today = date.today()
                    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                except ValueError:
                    pass
            translated.append(
                {
                    "orden_id": order.get("id", ""),
                    "orden_numero": order.get("order_number", ""),
                    "orden_estado": order.get("status") != "CANCELLED",
                    "orden_fecha": str(order.get("ordered_at", ""))[:10],
                    "orden_comentarios": order.get("clinical_notes") or "",
                    "oMic_persona": {
                        "persona_id": patient.get("id", ""),
                        "persona_hc": patient.get("medical_record_number", ""),
                        "persona_apellidos": patient.get("family_name", ""),
                        "persona_nombres": patient.get("given_name", ""),
                        "persona_fecha_nac": birth_date,
                        "persona_genero": patient.get("sex", ""),
                        "persona_edad": age,
                    },
                    "oMic_procedencia": {
                        "procedencia_id": origin.get("id", ""),
                        "procedencia_desc": origin.get("name", ""),
                    },
                    "oMic_servicio": {
                        "servicio_id": service.get("id", ""),
                        "servicio_desc": service.get("name", ""),
                    },
                    "oMic_medico": {
                        "medico_id": clinician.get("id", ""),
                        "medico_apellidos": clinician.get("family_name", ""),
                        "medico_nombres": clinician.get("given_name", ""),
                    },
                    "concat_temp_numero_examenes": len(order.get("items", [])),
                    "concat_temp_res_resultado": 0,
                    "concat_temp_res_priliminar": 0,
                    "concat_temp_res_final": 0,
                }
            )
        self.send_json({"data": translated, "resultado": True})

    def _load_catalog_maps(self, token: str, *, include_exams: bool = False, include_specimens: bool = False) -> dict:
        _, patient_page = api_req("GET", "/patients?page_size=100", token)
        _, origin_page = api_req("GET", "/catalogs/origins?page_size=100", token)
        _, service_page = api_req("GET", "/catalogs/services?page_size=100", token)
        _, clinician_page = api_req("GET", "/catalogs/clinicians?page_size=100", token)
        maps = {
            "patients": {item["id"]: item for item in (patient_page or {}).get("data", [])},
            "origins": {item["id"]: item for item in (origin_page or {}).get("data", [])},
            "services": {item["id"]: item for item in (service_page or {}).get("data", [])},
            "clinicians": {item["id"]: item for item in (clinician_page or {}).get("data", [])},
            "exams": {},
            "specimens": {},
        }
        if include_exams:
            _, exam_page = api_req("GET", "/catalogs/exams?active_only=false&page_size=100", token)
            maps["exams"] = {item["id"]: item for item in (exam_page or {}).get("data", [])}
        if include_specimens:
            _, specimen_page = api_req("GET", "/catalogs/specimen-types?active_only=false&page_size=100", token)
            maps["specimens"] = {item["id"]: item for item in (specimen_page or {}).get("data", [])}
        return maps

    def _legacy_order_row(self, order: dict, maps: dict) -> dict:
        patient = maps["patients"].get(order.get("patient_id"), {})
        origin = maps["origins"].get(order.get("origin_id"), {})
        service = maps["services"].get(order.get("service_id"), {})
        clinician = maps["clinicians"].get(order.get("clinician_id"), {})
        birth_date = patient.get("birth_date", "")
        age = ""
        if birth_date:
            try:
                born = date.fromisoformat(birth_date)
                today = date.today()
                age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            except ValueError:
                pass
        items = order.get("items", [])
        exam_names = []
        for item in items:
            exam = maps.get("exams", {}).get(item.get("exam_id"), {})
            exam_names.append(exam.get("name") or item.get("exam_id", ""))
        result_count = sum(1 for item in items if item.get("status") in {"IN_PROCESS", "RESULT_SAVED", "PRELIMINARY_VALIDATED", "FINAL_VALIDATED"})
        preliminary_count = sum(1 for item in items if item.get("status") in {"PRELIMINARY_VALIDATED", "FINAL_VALIDATED"})
        final_count = sum(1 for item in items if item.get("status") == "FINAL_VALIDATED")
        return {
            "orden_id": order.get("id", ""),
            "orden_numero": order.get("order_number", ""),
            "orden_estado": order.get("status") != "CANCELLED",
            "orden_fecha": str(order.get("ordered_at", ""))[:10],
            "orden_comentarios": order.get("clinical_notes") or "",
            "orden_temp1": "|".join(exam_names),
            "orden_temp2": len(items),
            "orden_temp3": preliminary_count,
            "orden_temp4": final_count,
            "concat_temp_numero_examenes": len(items),
            "concat_temp_res_resultado": result_count,
            "concat_temp_res_priliminar": preliminary_count,
            "concat_temp_res_final": final_count,
            "oMic_persona": {
                "persona_id": patient.get("id", ""),
                "persona_hc": patient.get("medical_record_number", ""),
                "persona_apellidos": patient.get("family_name", ""),
                "persona_nombres": patient.get("given_name", ""),
                "persona_fecha_nac": birth_date,
                "persona_genero": patient.get("sex", ""),
                "persona_edad": age,
            },
            "oMic_procedencia": {
                "procedencia_id": origin.get("id", ""),
                "procedencia_desc": origin.get("name", ""),
            },
            "oMic_servicio": {
                "servicio_id": service.get("id", ""),
                "servicio_desc": service.get("name", ""),
            },
            "oMic_medico": {
                "medico_id": clinician.get("id", ""),
                "medico_apellidos": clinician.get("family_name", ""),
                "medico_nombres": clinician.get("given_name", ""),
            },
        }

    def _proxy_consult_patient_orders(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        date_from = self._extract_query_param(request_path, "orden_fecha_ini")
        date_to = self._extract_query_param(request_path, "orden_fecha_fin")
        search = self._extract_query_param(request_path, "orden_buscar")
        query = ["page_size=100"]
        if date_from:
            query.append(f"from={quote(date_from, safe='')}")
        if date_to:
            query.append(f"to={quote(date_to, safe='')}")
        if search:
            query.append(f"search={quote(search, safe='')}")
        status, data = api_req("GET", f"/orders?{'&'.join(query)}", token)
        if status != 200 or not isinstance(data, dict):
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudieron cargar las ordenes"})
            return
        maps = self._load_catalog_maps(token, include_exams=True)
        rows = [self._legacy_order_row(order, maps) for order in data.get("data", [])]
        self.send_json({"data": rows, "resultado": True})

    def _proxy_order_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        patient_data = obj.get("oMic_persona") or {}
        hc = str(patient_data.get("persona_hc", "")).strip().upper()
        family_name = str(patient_data.get("persona_apellidos", "")).strip().upper()
        given_name = str(patient_data.get("persona_nombres", "")).strip().upper()
        birth_date = patient_data.get("persona_fecha_nac") or None
        sex = str(patient_data.get("persona_genero", "")).strip().upper()
        origin_id = str((obj.get("oMic_procedencia") or {}).get("procedencia_id", "")).strip()
        service_id = str((obj.get("oMic_servicio") or {}).get("servicio_id", "")).strip()
        clinician_id = str((obj.get("oMic_medico") or {}).get("medico_id", "")).strip()
        ordered_date = str(obj.get("orden_fecha", "")).strip()

        if not all((hc, family_name, given_name, birth_date, sex)):
            self.send_json({"resultado": False, "mensaje": "Complete todos los datos del paciente"})
            return
        if not origin_id or not service_id or not ordered_date:
            self.send_json({"resultado": False, "mensaje": "Complete fecha, procedencia y servicio"})
            return

        def resolve_catalog_id(api_path: str, value: str) -> str:
            catalog_status, catalog_page = api_req("GET", f"{api_path}?page_size=100", token)
            if catalog_status != 200 or not isinstance(catalog_page, dict):
                return ""
            normalized = value.lower()
            for item in catalog_page.get("data", []):
                if str(item.get("id", "")).lower() == normalized or str(item.get("code", "")).lower() == normalized:
                    return str(item.get("id", ""))
            return ""

        origin_id = resolve_catalog_id("/catalogs/origins", origin_id)
        service_id = resolve_catalog_id("/catalogs/services", service_id)
        clinician_id = resolve_catalog_id("/catalogs/clinicians", clinician_id) if clinician_id else ""
        if not origin_id:
            self.send_json({"resultado": False, "mensaje": "La procedencia seleccionada no existe o esta inactiva"})
            return
        if not service_id:
            self.send_json({"resultado": False, "mensaje": "El servicio seleccionado no existe o esta inactivo"})
            return
        if (obj.get("oMic_medico") or {}).get("medico_id") and not clinician_id:
            self.send_json({"resultado": False, "mensaje": "El medico seleccionado no existe o esta inactivo"})
            return

        patient_payload = {
            "medical_record_number": hc,
            "family_name": family_name,
            "given_name": given_name,
            "birth_date": birth_date,
            "sex": sex,
        }
        patient_status, patient_page = api_req(
            "GET", f"/patients?search={quote(hc, safe='')}&page_size=100", token
        )
        if patient_status != 200 or not isinstance(patient_page, dict):
            self.send_json({"resultado": False, "mensaje": "No se pudo consultar el paciente"})
            return
        patient = next(
            (
                item
                for item in patient_page.get("data", [])
                if str(item.get("medical_record_number", "")).upper() == hc
            ),
            None,
        )
        if patient:
            patient_id = patient["id"]
            patient_status, _ = api_req("PATCH", f"/patients/{patient_id}", token, patient_payload)
        else:
            patient_status, patient = api_req("POST", "/patients", token, patient_payload)
            patient_id = patient.get("id", "") if isinstance(patient, dict) else ""
        if patient_status not in (200, 201) or not patient_id:
            message = "El numero de HC ya esta registrado" if patient_status == 409 else "No se pudo guardar el paciente"
            self.send_json({"resultado": False, "mensaje": message})
            return

        payload = {
            "patient_id": patient_id,
            "ordered_at": f"{ordered_date}T00:00:00-05:00",
            "origin_id": origin_id,
            "service_id": service_id,
            "clinician_id": clinician_id or None,
            "clinical_notes": str(obj.get("orden_comentarios", "")).strip().upper() or None,
        }
        order_id = str(obj.get("orden_id", obj.get("order_id", ""))).strip()
        if order_id:
            update_payload = {key: value for key, value in payload.items() if key != "patient_id"}
            status, data = api_req("PATCH", f"/orders/{order_id}", token, update_payload)
        else:
            status, data = api_req("POST", "/orders", token, payload)
        if status in (200, 201):
            self.send_json(
                {
                    "resultado": True,
                    "mensaje": "Paciente y orden guardados correctamente",
                    "orden_id": data.get("id", "") if isinstance(data, dict) else "",
                    "orden_numero": data.get("order_number", "") if isinstance(data, dict) else "",
                }
            )
        elif status == 403:
            self.send_json({"resultado": False, "mensaje": "Su usuario no tiene permiso para guardar ordenes"})
        elif status == 422:
            self.send_json({"resultado": False, "mensaje": "Revise la fecha, procedencia, servicio y medico"})
        elif status == 404:
            detail = self._api_error(status, data)
            self.send_json({"resultado": False, "mensaje": detail if isinstance(detail, str) and detail else "No se encontro un dato requerido para la orden"})
        else:
            self.send_json({"resultado": False, "mensaje": f"No se pudo guardar la orden (HTTP {status})"})

    # ── ORDER DETAIL HANDLERS ──

    def _proxy_order_detail_exams(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        order_id = self._extract_query_param(request_path, "orden_id") or self._extract_query_param(request_path, "order_id")
        if not order_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/orders/{order_id}", token)
        if status == 200 and isinstance(data, dict):
            items = data.get("items", [])
            _, exam_page = api_req("GET", "/catalogs/exams?page_size=100", token)
            _, specimen_page = api_req("GET", "/catalogs/specimen-types?active_only=false&page_size=100", token)
            exams = {item["id"]: item for item in (exam_page or {}).get("data", [])}
            specimens = {item["id"]: item for item in (specimen_page or {}).get("data", [])}
            translated = []
            for item in items:
                exam = exams.get(item.get("exam_id"), {})
                specimen = specimens.get(item.get("specimen_type_id"), {})
                translated.append(
                    {
                        "orden_det_id": item.get("id", ""),
                        "orden_det_codebar": item.get("barcode", ""),
                        "orden_det_muestra_comentarios": item.get("specimen_notes") or "",
                        "fecha_muestra_toma": local_datetime_value(item.get("collection_at")),
                        "fecha_muestra_recepcion": local_datetime_value(item.get("received_at")),
                        "orden_det_estado": item.get("status", ""),
                        "oMic_examen": {
                            "examen_id": exam.get("id", ""),
                            "examen_codigo": exam.get("code", ""),
                            "examen_desc": exam.get("name", ""),
                        },
                        "oMic_muestra": {
                            "muestra_id": specimen.get("id", ""),
                            "muestra_cod_alfa": specimen.get("code", ""),
                            "muestra_desc": specimen.get("name", ""),
                        },
                    }
                )
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _find_order_and_items(self, token: str, *, order_id: str = "", item_id: str = "", barcode: str = "") -> list[tuple[dict, dict]]:
        order_id = "" if order_id in {"0", "ALL"} else order_id
        matches: list[tuple[dict, dict]] = []
        if order_id:
            status, order = api_req("GET", f"/orders/{quote(order_id, safe='')}", token)
            if status == 200 and isinstance(order, dict):
                for item in order.get("items", []):
                    if item_id and item.get("id") != item_id:
                        continue
                    if barcode and item.get("barcode") != barcode:
                        continue
                    matches.append((order, item))
                if matches or not item_id:
                    return matches
        if barcode:
            status, rows = api_req("GET", f"/result-worklist?search={quote(barcode, safe='')}", token)
            if status == 200 and isinstance(rows, list):
                for row in rows:
                    item = row.get("item") or {}
                    if item.get("barcode") == barcode:
                        order = row.get("order") or {}
                        if order.get("id"):
                            order_status, full_order = api_req("GET", f"/orders/{quote(order['id'], safe='')}", token)
                            if order_status == 200 and isinstance(full_order, dict):
                                return [(full_order, next((candidate for candidate in full_order.get("items", []) if candidate.get("id") == item.get("id")), item))]
        query = "page_size=100"
        if barcode:
            query += f"&search={quote(barcode, safe='')}"
        status, data = api_req("GET", f"/orders?{query}", token)
        if status == 200 and isinstance(data, dict):
            for order in data.get("data", []):
                for item in order.get("items", []):
                    if item_id and item.get("id") != item_id:
                        continue
                    if barcode and item.get("barcode") != barcode:
                        continue
                    if item_id or barcode:
                        return [(order, item)]
                    matches.append((order, item))
        return matches

    def _catalog_lookup_bundle(self, token: str) -> dict:
        maps = self._load_catalog_maps(token, include_exams=True, include_specimens=True)
        return maps

    def _barcode_label_contexts(self, token: str, path: str) -> list[dict]:
        request_path = self.path if hasattr(self, "path") else path
        order_id = self._extract_query_param(request_path, "orden_id") or self._extract_query_param(request_path, "order_id")
        item_id = self._extract_query_param(request_path, "orden_det_id") or self._extract_query_param(request_path, "item_id")
        barcode = self._extract_query_param(request_path, "orden_det_codebar") or self._extract_query_param(request_path, "barcode")
        if item_id == "ALL":
            item_id = ""
        pairs = self._find_order_and_items(token, order_id=order_id, item_id=item_id, barcode=barcode)
        maps = self._catalog_lookup_bundle(token)
        labels = []
        for order, item in pairs:
            patient = maps["patients"].get(order.get("patient_id"), {})
            exam = maps["exams"].get(item.get("exam_id"), {})
            specimen = maps["specimens"].get(item.get("specimen_type_id"), {})
            labels.append(
                {
                    "order": order,
                    "item": item,
                    "patient": patient,
                    "exam": exam,
                    "specimen": specimen,
                    "barcode": str(item.get("barcode", "")).upper(),
                }
            )
        return labels

    def _code39_svg(self, value: str) -> str:
        clean = "".join(ch if ch in CODE39_PATTERNS and ch != "*" else "-" for ch in uppercase_report_value(value))
        encoded = f"*{clean}*"
        narrow = 2
        wide = 5
        gap = 2
        height = 56
        x = 0
        rects = []
        for char in encoded:
            pattern = CODE39_PATTERNS.get(char, CODE39_PATTERNS["-"])
            for index, width_code in enumerate(pattern):
                width = wide if width_code == "w" else narrow
                if index % 2 == 0:
                    rects.append(f'<rect x="{x}" y="0" width="{width}" height="{height}" />')
                x += width
            x += gap
        return f'<svg class="barcode-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x} {height}" role="img" aria-label="{html.escape(clean)}">{"".join(rects)}</svg>'

    def _barcode_labels_html(self, labels: list[dict]) -> str:
        generated_at = datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M")

        def e(value: object) -> str:
            return html.escape(str(value or ""))

        label_html = []
        for label in labels:
            order = label["order"]
            item = label["item"]
            patient = label["patient"]
            exam = label["exam"]
            specimen = label["specimen"]
            barcode = label["barcode"]
            label_html.append(
                f"""
<section class="label">
  <div class="label-head">
    <strong>{e(INSTITUTION_NAME)}</strong>
    <span>{e(str(order.get('ordered_at', ''))[:10])}</span>
  </div>
  <div class="barcode">{self._code39_svg(barcode)}</div>
  <div class="barcode-text">{e(barcode)}</div>
  <div class="meta">
    <div><b>Orden</b><span>{e(order.get('order_number'))}</span></div>
    <div><b>HC</b><span>{e(patient.get('medical_record_number'))}</span></div>
    <div><b>Paciente</b><span>{e(patient.get('family_name'))}, {e(patient.get('given_name'))}</span></div>
    <div><b>Examen</b><span>{e(exam.get('name') or item.get('exam_id'))}</span></div>
    <div><b>Muestra</b><span>{e(specimen.get('name') or item.get('specimen_type_id'))}</span></div>
  </div>
</section>"""
            )
        return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Etiquetas de codigo de barras - MUFFIN</title>
<style>
body{{background:#f3f8f6;color:#173d43;font-family:Arial,Helvetica,sans-serif;margin:0;padding:18px}}
.toolbar{{align-items:center;display:flex;gap:10px;justify-content:space-between;margin:0 auto 14px;max-width:720px}}
.toolbar h1{{font-size:18px;margin:0}}button{{background:#167d86;border:0;border-radius:5px;color:#fff;font-weight:700;padding:8px 12px}}
.sheet{{display:grid;gap:14px;margin:0 auto;max-width:720px}}
.label{{background:#fff;border:1px solid #b8d0cc;border-radius:6px;break-inside:avoid;padding:12px;page-break-inside:avoid}}
.label-head{{display:flex;font-size:12px;justify-content:space-between;margin-bottom:8px;text-transform:uppercase}}
.barcode{{display:flex;justify-content:center;margin:5px 0}}.barcode-svg{{height:56px;max-width:100%;width:100%}}
.barcode-text{{font-size:16px;font-weight:700;letter-spacing:.08em;text-align:center}}
.meta{{display:grid;font-size:11px;gap:4px;grid-template-columns:repeat(2,1fr);margin-top:8px}}
.meta div{{border-top:1px solid #d5e5e2;padding-top:4px}}.meta b{{color:#607477;display:block;font-size:9px;text-transform:uppercase}}
.meta span{{font-weight:700}}.foot{{color:#607477;font-size:10px;margin:10px auto 0;max-width:720px;text-align:right}}
@media print{{body{{background:#fff;padding:0}}.toolbar,.foot{{display:none}}.sheet{{display:block;max-width:none}}.label{{border:0;border-radius:0;margin:0;padding:6mm;width:88mm}}}}
</style>
</head>
<body>
<div class="toolbar"><h1>Etiquetas de codigo de barras</h1><button onclick="window.print()">Imprimir</button></div>
<main class="sheet">{''.join(label_html)}</main>
<div class="foot">Generado por MUFFIN {e(generated_at)}</div>
</body>
</html>"""

    def _proxy_barcode_print(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        labels = self._barcode_label_contexts(token, request_path)
        if not labels:
            if self._extract_query_param(request_path, "formato") == "html":
                self._send_html_message("Codigo de barras", "No se encontro la orden o muestra solicitada.")
            else:
                self.send_json({"resultado": False, "mensaje": "No se encontro la orden o muestra solicitada"})
            return
        if self._extract_query_param(request_path, "formato") == "html":
            for label in labels:
                item_id = label["item"].get("id", "")
                if item_id:
                    api_req("POST", "/print-jobs", token, {"order_item_id": item_id, "kind": "LABEL", "details": f"Etiqueta {label['barcode']}"})
            self.send_bytes(self._barcode_labels_html(labels).encode("utf-8"), 200, "text/html; charset=utf-8", cache_control="no-store")
            return
        self.send_json({"resultado": True, "mensaje": "Etiqueta lista para imprimir"})

    def _proxy_destination_order_search(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        search = self._extract_query_param(request_path, "orden_numero").strip()
        if not search:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/orders?search={quote(search, safe='')}&page_size=100", token)
        orders = data.get("data", []) if status == 200 and isinstance(data, dict) else []
        normalized = normalize_match_key(search)
        if not orders:
            status, data = api_req("GET", "/orders?page_size=100", token)
            if status == 200 and isinstance(data, dict):
                orders = [
                    order
                    for order in data.get("data", [])
                    if normalize_match_key(order.get("order_number", "")) == normalized
                    or any(normalize_match_key(item.get("barcode", "")) == normalized for item in order.get("items", []))
                ]
        if not orders:
            self.send_json({"data": [], "resultado": True})
            return
        maps = self._load_catalog_maps(token, include_exams=True)
        rows = []
        for order in orders:
            row = self._legacy_order_row(order, maps)
            row["orden_seach_busqueda_verificar"] = (
                "bus_codebar"
                if any(normalize_match_key(item.get("barcode", "")) == normalized for item in order.get("items", []))
                else "bus_orden"
            )
            rows.append(row)
        self.send_json({"data": rows, "resultado": True})

    def _destination_map(self, token: str) -> dict:
        status, data = api_req("GET", "/catalogs/destinations?active_only=false&page_size=100", token)
        return {item["id"]: item for item in (data or {}).get("data", [])} if status == 200 and isinstance(data, dict) else {}

    def _microbiology_destination_id(self, token: str) -> str:
        destinations = self._destination_map(token)
        for item in destinations.values():
            if str(item.get("code", "")).upper() == "MICROBIOLOGY_BENCH":
                return item.get("id", "")
        return next((item.get("id", "") for item in destinations.values() if item.get("is_active", True)), "")

    def _proxy_destination_order_detail_list(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        order_id = self._extract_query_param(request_path, "orden_id")
        barcode = self._extract_query_param(request_path, "orden_det_codebar")
        labels = self._barcode_label_contexts(
            token,
            f"/MUFFIN/Mic_orden/RegistrarPrinterCodebar?orden_id={quote(order_id, safe='')}&orden_det_id={'ALL' if barcode == 'ALL' else ''}&orden_det_codebar={quote('' if barcode == 'ALL' else barcode, safe='')}",
        )
        if not labels and barcode and barcode != "ALL":
            labels = self._barcode_label_contexts(token, f"/MUFFIN/Mic_orden/RegistrarPrinterCodebar?orden_det_codebar={quote(barcode, safe='')}")
        destinations = self._destination_map(token)
        rows = []
        for label in labels:
            item = label["item"]
            barcode_value = item.get("barcode", "")
            status, events = api_req("GET", f"/order-items/{quote(item.get('id', ''), safe='')}/events", token)
            if status != 200 or not isinstance(events, list):
                events = []
            for event in events:
                details = event.get("details") or {}
                destination = destinations.get(details.get("destination_id") or item.get("destination_id"), {})
                rows.append(
                    {
                        "desti_orden_det_id": event.get("id", ""),
                        "desti_orden_det_fecha": local_datetime_value(event.get("occurred_at")).replace("T", " "),
                        "desti_orden_det_user": event.get("performed_by") or "",
                        "desti_orden_det_comentarios": details.get("reason") or details.get("location") or details.get("restored_status") or "",
                        "oMic_orden_detalle": {"orden_det_id": item.get("id", ""), "orden_det_codebar": barcode_value},
                        "oMic_destinos": {
                            "destinos_desc": destination.get("name") or event.get("event_type", ""),
                            "destinos_orden_verificacion_orden": event.get("event_type", ""),
                            "destinos_orden_verificacion_requiere": "0",
                        },
                    }
                )
        self.send_json({"data": rows, "resultado": True})

    def _proxy_destination_order_verify(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        item_data = obj.get("oMic_orden_detalle") or {}
        barcode = str(item_data.get("orden_det_codebar", "")).strip()
        order_data = item_data.get("oMic_orden") or {}
        order_id = str(order_data.get("orden_id", "")).strip()
        labels = self._barcode_label_contexts(token, f"/MUFFIN/Mic_orden/RegistrarPrinterCodebar?orden_id={quote(order_id, safe='')}&orden_det_codebar={quote(barcode, safe='')}")
        if not labels:
            labels = self._barcode_label_contexts(token, f"/MUFFIN/Mic_orden/RegistrarPrinterCodebar?orden_det_codebar={quote(barcode, safe='')}")
        if not labels:
            self.send_json({"resultado": False, "mensaje": "No se encontro la muestra para verificar"})
            return
        item = labels[0]["item"]
        if item.get("status") in {"RECEIVED", "IN_PROCESS", "RESULT_SAVED", "PRELIMINARY_VALIDATED", "FINAL_VALIDATED"}:
            self.send_json({"resultado": True, "mensaje": "Muestra ya verificada"})
            return
        destination_id = self._microbiology_destination_id(token)
        if not destination_id:
            self.send_json({"resultado": False, "mensaje": "No existe destino activo para microbiologia"})
            return
        now = datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S-05:00")
        payload = {
            "destination_id": destination_id,
            "collection_at": item.get("collection_at") or now,
            "received_at": now,
            "specimen_notes": str(obj.get("desti_orden_det_comentarios", "")).strip() or item.get("specimen_notes"),
        }
        status, data = api_req("POST", f"/order-items/{quote(item.get('id', ''), safe='')}/receive", token, payload)
        if status == 200:
            self.send_json({"resultado": True, "mensaje": "Muestra verificada correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo verificar la muestra (HTTP {status})"})

    def _proxy_destination_order_detail_save(self, token: str) -> None:
        self.send_json({"resultado": False, "mensaje": "El historial de verificacion es trazable y no se edita. Registre una nueva verificacion si corresponde."}, 409)

    def _proxy_destination_order_detail_delete(self, token: str) -> None:
        self.send_json({"resultado": False, "mensaje": "El historial de verificacion no se elimina por trazabilidad."}, 409)

    def _proxy_order_item_add(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        order_id = str((obj.get("oMic_orden") or {}).get("orden_id", obj.get("orden_id", ""))).strip()
        exam_id = str((obj.get("oMic_examen") or {}).get("examen_id", obj.get("examen_id", ""))).strip()
        specimen_data = obj.get("oMic_muestra") or {}
        specimen_id = str(specimen_data.get("muestra_id", specimen_data.get("muestra_cod_alfa", ""))).strip()
        if not order_id or not exam_id or not specimen_id:
            self.send_json({"resultado": False, "mensaje": "Seleccione orden, examen y muestra terminal"})
            return

        def resolve_id(api_path: str, value: str) -> str:
            catalog_status, catalog_page = api_req("GET", f"{api_path}?page_size=100", token)
            if catalog_status != 200 or not isinstance(catalog_page, dict):
                return ""
            normalized = value.lower()
            for item in catalog_page.get("data", []):
                if str(item.get("id", "")).lower() == normalized or str(item.get("code", "")).lower() == normalized:
                    return str(item.get("id", ""))
            return ""

        exam_id = resolve_id("/catalogs/exams", exam_id)
        specimen_id = resolve_id("/catalogs/specimen-types", specimen_id)
        if not exam_id or not specimen_id:
            self.send_json({"resultado": False, "mensaje": "El examen o la muestra seleccionada no existe"})
            return
        payload = {
            "exam_id": exam_id,
            "specimen_type_id": specimen_id,
            "specimen_notes": str(obj.get("orden_det_muestra_comentarios", "")).strip().upper() or None,
        }
        collection_at = str(obj.get("fecha_muestra_toma", "")).strip()
        reception_at = str(obj.get("fecha_muestra_recepcion", "")).strip()
        if collection_at:
            payload["collection_at"] = f"{collection_at}:00-05:00" if len(collection_at) == 16 else f"{collection_at}-05:00"
        destination_id = resolve_id("/catalogs/destinations", "MICROBIOLOGY_BENCH") if reception_at else ""
        if reception_at and not destination_id:
            self.send_json({"resultado": False, "mensaje": "No se encontro el destino de microbiologia para recibir la muestra"})
            return
        status, data = api_req("POST", f"/orders/{order_id}/items", token, payload)
        if status in (200, 201):
            if reception_at and isinstance(data, dict):
                received_payload = {
                    "received_at": f"{reception_at}:00-05:00" if len(reception_at) == 16 else f"{reception_at}-05:00",
                    "destination_id": destination_id,
                    "specimen_notes": payload["specimen_notes"],
                }
                receive_status, receive_data = api_req(
                    "POST", f"/order-items/{data.get('id', '')}/receive", token, received_payload
                )
                if receive_status not in (200, 201):
                    self.send_json(
                        {
                            "resultado": True,
                            "mensaje": "Examen agregado; la muestra quedo pendiente de recepcion",
                            "advertencia": self._api_error(receive_status, receive_data) or f"HTTP {receive_status}",
                        }
                    )
                    return
            self.send_json({"resultado": True, "mensaje": "Examen y muestra agregados a la orden"})
        elif status == 422:
            self.send_json({"resultado": False, "mensaje": "Seleccione una muestra terminal permitida para el examen"})
        else:
            self.send_json({"resultado": False, "mensaje": f"No se pudo agregar el examen (HTTP {status})"})

    def _proxy_order_item_delete(self, token: str) -> None:
        body = self._read_body()
        request_path = self.path if hasattr(self, "path") else ""
        item_id = (
            (body or {}).get("item_id", "")
            or (body or {}).get("detalle_id", "")
            or self._extract_query_param(request_path, "orden_det_id")
            or self._extract_query_param(request_path, "item_id")
        )
        if not item_id:
            self.send_json({"resultado": False, "mensaje": "item_id requerido"})
            return
        status, data = api_req("POST", f"/order-items/{item_id}/cancel", token, {"reason": "Eliminado desde frontend"})
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Item cancelado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _translate_result_worklist_item(self, row: dict) -> dict:
        item = row.get("item") or {}
        order = row.get("order") or {}
        patient = row.get("patient") or {}
        exam = row.get("exam") or {}
        specimen = row.get("specimen") or {}
        origin = row.get("origin") or {}
        service = row.get("service") or {}
        clinician = row.get("clinician") or {}
        result = row.get("result") or {}
        birth_date = patient.get("birth_date", "")
        age = ""
        if birth_date:
            try:
                born = date.fromisoformat(birth_date)
                today = date.today()
                age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            except ValueError:
                pass
        return {
            "orden_det_id": item.get("id", ""),
            "orden_det_codebar": item.get("barcode", ""),
            "orden_det_estado": item.get("status", ""),
            "orden_det_muestra_comentarios": item.get("specimen_notes") or "",
            "orden_det_muestra_recepcion_estado": item.get("status") not in {"REGISTERED", "COLLECTED"},
            "fecha_muestra_toma": local_datetime_value(item.get("collection_at")),
            "fecha_muestra_recepcion": local_datetime_value(item.get("received_at")),
            "fecha_proc_resultado": str(result.get("saved_at") or "")[:16],
            "fecha_proc_preliminar": str(result.get("preliminary_at") or "")[:16],
            "fecha_proc_final": str(result.get("final_at") or "")[:16],
            "oMic_examen": {
                "examen_id": exam.get("id", ""),
                "examen_codigo": exam.get("code", ""),
                "examen_desc": exam.get("name", ""),
                "area_id": exam.get("laboratory_area_id", ""),
                "examen_analizador_send": exam.get("sends_to_analyzer", False),
                "examen_recuento": exam.get("requires_colony_count", False),
            },
            "oMic_muestra": {
                "muestra_id": specimen.get("id", ""),
                "muestra_cod_alfa": specimen.get("code", ""),
                "muestra_desc": specimen.get("name", ""),
            },
            "oMic_orden": {
                "orden_id": order.get("id", ""),
                "orden_numero": order.get("order_number", ""),
                "orden_fecha": str(order.get("ordered_at", ""))[:10],
                "orden_comentarios": order.get("clinical_notes") or "",
                "orden_tipo_loc": CARE_SETTING_LABELS.get(order.get("care_setting"), "DESCONOCIDO"),
                "oMic_persona": {
                    "persona_id": patient.get("id", ""),
                    "persona_hc": patient.get("medical_record_number", ""),
                    "persona_apellidos": patient.get("family_name", ""),
                    "persona_nombres": patient.get("given_name", ""),
                    "persona_fecha_nac": birth_date,
                    "persona_genero": patient.get("sex", ""),
                    "persona_edad": age,
                },
                "oMic_procedencia": {
                    "procedencia_id": origin.get("id", ""),
                    "procedencia_desc": origin.get("name", ""),
                },
                "oMic_servicio": {
                    "servicio_id": service.get("id", ""),
                    "servicio_desc": service.get("name", ""),
                },
                "oMic_medico": {
                    "medico_id": clinician.get("id", ""),
                    "medico_apellidos": clinician.get("family_name", ""),
                    "medico_nombres": clinician.get("given_name", ""),
                },
            },
        }

    def _proxy_result_worklist(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        date_from = self._extract_query_param(request_path, "orden_fecha_ini")
        date_to = self._extract_query_param(request_path, "orden_fecha_fin")
        search = self._extract_query_param(request_path, "orden_buscar")
        selected_area = self._extract_query_param(request_path, "orden_area")
        selected_filter = self._extract_query_param(request_path, "orden_filtro") or "ALL"
        selected_culture_result = selected_area.upper()
        culture_result_filters = {"POSITIVO", "NEGATIVO", "NO_TRAJO_MUESTRA", "MUESTRA_INADECUADA", "SIN_RESULTADO"}
        status_filters = {"Nuevos", "Recepcionado", "Guardados", "Preliminar", "Final", "Instrumento"}
        query = []
        if date_from:
            query.append(f"from={quote(date_from, safe='')}")
        if date_to:
            query.append(f"to={quote(date_to, safe='')}")
        if search:
            query.append(f"search={quote(search, safe='')}")
        status, data = api_req("GET", f"/result-worklist?{'&'.join(query)}", token)
        if status != 200 or not isinstance(data, list):
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudo cargar la bandeja de resultados"})
            return
        translated = [self._translate_result_worklist_item(row) for row in data]
        if selected_culture_result in culture_result_filters:
            translated = [
                row
                for row in translated
                if self._matches_culture_result_filter(token, row["orden_det_id"], selected_culture_result)
            ]
        elif selected_area and selected_area not in {"ALL", "0"}:
            translated = [row for row in translated if row["oMic_examen"]["area_id"] == selected_area]
        if selected_filter and selected_filter not in {"ALL", "0"} and selected_filter not in status_filters:
            translated = [
                row
                for row in translated
                if row["oMic_orden"]["oMic_procedencia"]["procedencia_id"] == selected_filter
            ]
        elif selected_filter == "Nuevos":
            translated = [row for row in translated if not row["fecha_proc_resultado"]]
        elif selected_filter == "Recepcionado":
            translated = [row for row in translated if row["orden_det_estado"] == "RECEIVED"]
        elif selected_filter == "Guardados":
            translated = [row for row in translated if row["orden_det_estado"] in {"IN_PROCESS", "RESULT_SAVED"}]
        elif selected_filter == "Preliminar":
            translated = [row for row in translated if row["orden_det_estado"] == "PRELIMINARY_VALIDATED"]
        elif selected_filter == "Final":
            translated = [row for row in translated if row["orden_det_estado"] == "FINAL_VALIDATED"]
        elif selected_filter == "Instrumento":
            translated = [row for row in translated if row["oMic_examen"]["examen_analizador_send"]]
        self.send_json({"data": translated, "resultado": True})

    def _matches_culture_result_filter(self, token: str, item_id: str, selected_filter: str) -> bool:
        value = self._culture_result_code(token, item_id)
        if selected_filter == "SIN_RESULTADO":
            return not value
        return value == selected_filter

    def _culture_result_code(self, token: str, item_id: str) -> str:
        status, data = api_req("GET", f"/order-items/{quote(item_id, safe='')}/result", token)
        if status != 200 or not isinstance(data, dict):
            return ""
        for parameter in data.get("values", []):
            if parameter.get("code") != "CULTURE_RESULT":
                continue
            value = str(parameter.get("value_code") or "").strip().upper()
            if value:
                return value
            text_value = str(parameter.get("value_text") or "").strip().upper().replace(" ", "_")
            return {
                "NO_TRAJO_MUESTRA": "NO_TRAJO_MUESTRA",
                "MUESTRA_INADECUADA": "MUESTRA_INADECUADA",
                "POSITIVO": "POSITIVO",
                "NEGATIVO": "NEGATIVO",
            }.get(text_value, text_value)
        return ""

    def _proxy_result_item_sample(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        item_id = self._extract_query_param(request_path, "orden_det_id") or self._extract_query_param(request_path, "item_id")
        if not item_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/result-worklist?item_id={quote(item_id, safe='')}", token)
        if status == 200 and isinstance(data, list):
            self.send_json({"data": [self._translate_result_worklist_item(row) for row in data], "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudo cargar la muestra"})

    def _proxy_order_item_results(self, token: str, path: str) -> None:
        item_id = self._extract_query_param(path, "item_id") or self._extract_query_param(path, "detalle_id")
        if not item_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/order-items/{item_id}/result", token)
        if status == 200 and isinstance(data, dict):
            self.send_json({"data": [data], "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_order_item_sample_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        item_id = obj.get("orden_det_id", obj.get("item_id", obj.get("detalle_id", "")))
        if not item_id:
            self.send_json({"resultado": False, "mensaje": "item_id requerido"})
            return
        payload = {
            "specimen_notes": str(obj.get("orden_det_muestra_comentarios", "")).strip().upper() or None,
        }
        collection_at = str(obj.get("fecha_muestra_toma", "")).strip()
        received_at = str(obj.get("fecha_muestra_recepcion", "")).strip()
        if collection_at:
            payload["collection_at"] = f"{collection_at}:00-05:00" if len(collection_at) == 16 else f"{collection_at}-05:00"
        if received_at:
            payload["received_at"] = f"{received_at}:00-05:00" if len(received_at) == 16 else f"{received_at}-05:00"
        status, data = api_req("PATCH", f"/order-items/{item_id}/specimen-details", token, payload)
        if status == 200:
            self.send_json({"resultado": True, "mensaje": "Datos de la muestra actualizados"})
        else:
            message = self._api_error(status, data) or f"Error HTTP {status}"
            self.send_json({"resultado": False, "mensaje": message})

    # ── RESULTS HANDLERS ──

    def _proxy_result_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        item_id = obj.get("orden_det_id", obj.get("item_id", obj.get("detalle_id", "")))
        if not item_id:
            self.send_json({"resultado": False, "mensaje": "item_id requerido"})
            return
        form_status, form = api_req("GET", f"/order-items/{item_id}/result", token)
        if form_status != 200 or not isinstance(form, dict):
            self.send_json({"resultado": False, "mensaje": "No se pudo cargar la configuracion del resultado"})
            return
        control_ids = str(obj.get("temporal1", "")).split("|")
        control_values = str(obj.get("temporal2", "")).split("|")
        submitted = {}
        for control_id, value in zip(control_ids, control_values):
            if not control_id:
                continue
            normalized_value = "" if value is None or str(value).strip().lower() in {"null", "undefined"} else value
            submitted[control_id] = normalized_value
        translated_values = []
        for parameter in form.get("values", []):
            parameter_id = parameter.get("parameter_definition_id", "")
            value = submitted.get(parameter_id, "")
            translated = {"parameter_definition_id": parameter_id}
            if parameter.get("value_type") == "SELECT":
                translated["value_code"] = value or None
            else:
                translated["value_text"] = value or None
            translated_values.append(translated)
        validation_type = int(obj.get("other1", 0) or 0)
        payload = {"values": translated_values, "ready_for_validation": validation_type in {1, 2}}
        status, data = api_req("PUT", f"/order-items/{item_id}/result", token, payload)
        if status not in (200, 201):
            message = (
                "La muestra debe estar recibida antes de registrar resultados"
                if status == 409
                else self._api_error(status, data) or "Revise los valores requeridos del resultado"
            )
            self.send_json({"resultado": False, "mensaje": message})
            return
        if validation_type in {1, 2}:
            status, data = api_req("POST", f"/order-items/{item_id}/result/preliminary-validation", token)
        if status in (200, 201) and validation_type == 2:
            status, data = api_req("POST", f"/order-items/{item_id}/result/final-validation", token)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Resultado guardado correctamente"})
        else:
            self.send_json({"resultado": False, "mensaje": "El resultado se guardo, pero no pudo validarse"})

    def _proxy_result_delete(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        item_id = (
            self._extract_query_param(request_path, "orden_det_id")
            or self._extract_query_param(request_path, "item_id")
            or self._extract_query_param(request_path, "detalle_id")
        )
        if not item_id:
            self.send_json({"resultado": False, "mensaje": "Orden detalle requerida"})
            return
        status, data = api_req("DELETE", f"/order-items/{quote(item_id, safe='')}/result", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Resultado eliminado correctamente"})
        elif status == 403:
            self.send_json({"resultado": False, "mensaje": "Su usuario no tiene permiso para eliminar este resultado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"No se pudo eliminar el resultado (HTTP {status})"})

    def _proxy_result_get_by_order(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        item_id = (
            self._extract_query_param(request_path, "orden_det_id")
            or self._extract_query_param(request_path, "item_id")
            or self._extract_query_param(request_path, "detalle_id")
        )
        if not item_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/order-items/{item_id}/result", token)
        if status == 200 and isinstance(data, dict):
            parameters = []
            for parameter in data.get("values", []):
                parameter_id = parameter.get("parameter_definition_id", "")
                parameter_name = html.escape(str(parameter.get("name", "")))
                parameter_code = parameter.get("code", "")
                required = " required" if parameter.get("is_required") else ""
                if parameter_code == "CULTURE_NITRITE":
                    required = ""
                value_type = parameter.get("value_type")
                if parameter_code in SUPPRESSED_RESULT_PARAMETERS:
                    continue
                if value_type == "SELECT":
                    options = RESULT_PARAMETER_OPTION_OVERRIDES.get(
                        parameter_code,
                        select_options_from_schema(parameter.get("options_schema")),
                    )
                    options_html = "".join(
                        f'<option value="{html.escape(code)}">{html.escape(label)}</option>'
                        for code, label in options
                    )
                    control_html = f'<select id="{parameter_id}" class="form-control form-control-sm"{required}>{options_html}</select>'
                    parameter_type = "COMBO_BOX"
                    current_value = parameter.get("value_code") or ""
                elif value_type == "LONG_TEXT":
                    control_html = f'<textarea id="{parameter_id}" class="form-control form-control-sm"{required}></textarea>'
                    parameter_type = "TEXT_AREA"
                    current_value = parameter.get("value_text") or ""
                else:
                    input_type = "date" if value_type == "DATE" else "text"
                    control_html = f'<input type="{input_type}" id="{parameter_id}" class="form-control form-control-sm"{required}>'
                    parameter_type = "TEXT"
                    current_value = parameter.get("value_text") or ""
                wrapper_classes = ["form-group"]
                wrapper_style = ""
                if parameter_code in {
                    "CULTURE_GRAM",
                    "CULTURE_NITRITE",
                    "CULTURE_COLONY_COUNT",
                }:
                    wrapper_classes.append("muffin-culture-positive-only")
                    wrapper_style = ' style="display:none"'
                parameters.append(
                    {
                        "param_cod": parameter_id,
                        "param_tipo": parameter_type,
                        "param_value1": current_value,
                        "param_html": f'<div class="{" ".join(wrapper_classes)}"{wrapper_style}><label for="{parameter_id}">{parameter_name}</label>{control_html}</div>',
                    }
                )
            self.send_json({"data": parameters, "resultado": True, "estado": data.get("status", "NOT_STARTED")})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_legacy_report_params(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        item_id = (
            self._extract_query_param(request_path, "IdMic_orden_detalle")
            or self._extract_query_param(request_path, "orden_det_id")
            or self._extract_query_param(request_path, "item_id")
        )
        if not item_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/order-items/{quote(item_id, safe='')}/result", token)
        rows = []
        if status == 200 and isinstance(data, dict):
            for parameter in data.get("values", []):
                if parameter.get("code") in SUPPRESSED_RESULT_PARAMETERS:
                    continue
                value = parameter.get("value_text") if parameter.get("value_text") is not None else parameter.get("value_code")
                if value in (None, ""):
                    continue
                rows.append({"param_desc": uppercase_report_value(parameter.get("name")), "param_value1": uppercase_report_value(value)})
        self.send_json({"data": rows, "resultado": True})

    def _proxy_legacy_report_panels(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        barcode = self._extract_query_param(request_path, "orden_det_codebar") or self._extract_query_param(request_path, "codebar")
        context = self._result_context(token, barcode=barcode) if barcode else None
        item_id = ((context or {}).get("item") or {}).get("id", "")
        if not item_id:
            self.send_json({"data": [], "resultado": True})
            return
        result_status, result = api_req("GET", f"/order-items/{quote(item_id, safe='')}/result", token)
        if result_status != 200 or not isinstance(result, dict) or not result.get("id"):
            self.send_json({"data": [], "resultado": True})
            return
        isolate_status, isolates = api_req("GET", f"/results/{quote(result['id'], safe='')}/isolates", token)
        rows = []
        if isolate_status == 200 and isinstance(isolates, list):
            for isolate in isolates:
                organism = isolate.get("organism") or {}
                colony = isolate.get("colony_count_option") or {}
                rows.append(
                    {
                        "respanel_id": isolate.get("id", ""),
                        "respanel_organismo_desc": uppercase_report_value(organism.get("name") or isolate.get("organism_id")),
                        "respanel_recuento": uppercase_report_value(colony.get("name") or isolate.get("colony_count_option_id")),
                        "respanel_organismo_fenotipo": uppercase_report_value(isolate.get("phenotype")),
                        "respanel_organismo_comentario": uppercase_report_value(isolate.get("comment")),
                    }
                )
        self.send_json({"data": rows, "resultado": True})

    def _proxy_legacy_report_panel_atb(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        isolate_id = self._extract_query_param(request_path, "respanel_id") or self._extract_query_param(request_path, "isolate_id")
        if not isolate_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, rows = api_req("GET", f"/isolates/{quote(isolate_id, safe='')}/antimicrobial-results", token)
        translated = []
        if status == 200 and isinstance(rows, list):
            for row in rows:
                if not row.get("is_reportable", True):
                    continue
                antibiotic = row.get("antibiotic") or {}
                translated.append(
                    {
                        "respaneldet_anti_desc": uppercase_report_value(antibiotic.get("name") or row.get("antibiotic_id")),
                        "respaneldet_anti_valor": report_ast_value(row.get("method"), row.get("mic_value")),
                        "respaneldet_anti_inter": uppercase_report_value(row.get("interpretation")),
                        "respaneldet_anti_metodo": report_ast_method_label(row.get("method")),
                        "respaneldet_anti_macanismo": 1 if row.get("mechanism") else 0,
                    }
                )
        self.send_json({"data": translated, "resultado": True})

    def _proxy_result_report(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        order_id = (
            self._extract_query_param(request_path, "orden_id")
            or self._extract_query_param(request_path, "order_id")
            or self._extract_query_param(request_path, "id")
        )
        item_id = (
            self._extract_query_param(request_path, "IdMic_orden_detalle")
            or self._extract_query_param(request_path, "orden_det_id")
            or self._extract_query_param(request_path, "item_id")
        )

        order: dict = {}
        if order_id:
            status, data = api_req("GET", f"/orders/{quote(order_id, safe='')}", token)
            if status != 200 or not isinstance(data, dict):
                self._send_report_error("No se pudo cargar la orden solicitada.")
                return
            order = data
        elif item_id:
            context = self._result_context(token, item_id=item_id)
            order_id = ((context or {}).get("order") or {}).get("id", "")
            if order_id:
                status, data = api_req("GET", f"/orders/{quote(order_id, safe='')}", token)
                order = data if status == 200 and isinstance(data, dict) else {}
        else:
            self._send_report_error("orden_id requerido.")
            return

        raw_items = order.get("items", []) if isinstance(order, dict) else []
        if item_id:
            raw_items = [item for item in raw_items if item.get("id") == item_id]
        report_items = [self._build_report_item(token, item) for item in raw_items]
        report_items = [item for item in report_items if item]
        if not report_items:
            self._send_report_error("La orden no tiene resultados disponibles para reportar.")
            return

        first = report_items[0]["translated"]
        order_info = first.get("oMic_orden", {})
        patient = order_info.get("oMic_persona", {})
        clinician = order_info.get("oMic_medico", {})
        status_values = {
            report_status_label(
                item["result"].get("status") or item["translated"].get("orden_det_estado", ""),
                culture_result_code(item["result"]),
            )
            for item in report_items
        }
        status_label = " / ".join(sorted(value for value in status_values if value)) or "EN PROCESO"
        final_notice = "" if status_values <= {"FINALIZADO", "RECHAZADO"} else "<div class='notice'>Constancia emitida con resultado en proceso. Verifique la validación final antes de usarla como informe definitivo.</div>"

        def e(value: object) -> str:
            return html.escape(str(value or ""))

        item_sections = "".join(self._render_report_item(item) for item in report_items)
        signatures_html = render_report_signatures(self._report_signer(token, report_items))
        generated_at = datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M")
        body = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de resultados - {e(order_info.get('orden_numero', order.get('order_number', '')))}</title>
<style>
:root {{ color-scheme: light; --ink:#1f3438; --muted:#607477; --line:#b9cdca; --teal:#167d86; --soft:#eef6f3; }}
* {{ box-sizing: border-box; }}
body {{ color: var(--ink); font-family: Arial, Helvetica, sans-serif; font-size: 12px; line-height: 1.35; margin: 0; padding: 22px; }}
.sheet {{ border: 1px solid var(--line); margin: 0 auto; max-width: 940px; padding: 22px; }}
.topbar {{ align-items: center; border-bottom: 3px solid var(--teal); display: flex; gap: 14px; padding-bottom: 12px; }}
.topbar img {{ border-radius: 50%; height: 54px; object-fit: cover; width: 54px; }}
.brand h1 {{ font-size: 20px; letter-spacing: .04em; margin: 0; }}
.brand p {{ color: var(--muted); margin: 2px 0 0; }}
.actions {{ margin-left: auto; }}
button {{ background: var(--teal); border: 0; border-radius: 5px; color: white; cursor: pointer; font-weight: 700; padding: 8px 12px; }}
.notice {{ background: #fff5d6; border: 1px solid #e4c36c; border-radius: 5px; color: #6f5315; font-weight: 700; margin: 12px 0; padding: 8px 10px; }}
.grid {{ display: grid; gap: 7px 18px; grid-template-columns: repeat(3, 1fr); margin: 14px 0; }}
.field strong {{ color: var(--muted); display: block; font-size: 10px; letter-spacing: .04em; text-transform: uppercase; }}
h2 {{ background: var(--soft); border-left: 5px solid var(--teal); font-size: 14px; margin: 18px 0 8px; padding: 7px 9px; }}
h3 {{ color: var(--teal); font-size: 12px; margin: 12px 0 6px; }}
table {{ border-collapse: collapse; margin: 6px 0 12px; width: 100%; }}
th, td {{ border: 1px solid var(--line); padding: 6px 7px; text-align: left; vertical-align: top; }}
th {{ background: var(--soft); color: var(--ink); font-size: 10px; letter-spacing: .04em; text-transform: uppercase; }}
.empty {{ color: var(--muted); font-style: italic; padding: 6px 0 12px; }}
.signature-panel {{ border-top: 1px solid var(--line); break-inside: avoid; margin-top: 20px; padding-top: 14px; page-break-inside: avoid; }}
.signature-title {{ color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: .08em; margin-bottom: 8px; text-transform: uppercase; }}
.signature-grid {{ display: grid; gap: 18px; grid-template-columns: minmax(0, 1fr); justify-items: center; }}
.signature-card {{ color: var(--ink); max-width: 460px; min-height: 150px; text-align: center; width: 100%; }}
.signature-image {{ align-items: center; display: flex; height: 88px; justify-content: center; margin: 0 auto 5px; max-width: 330px; }}
.signature-image img {{ display: block; max-height: 88px; max-width: 100%; mix-blend-mode: multiply; object-fit: contain; }}
.signature-line {{ border-top: 1px solid var(--ink); margin: 4px auto 6px; width: 72%; }}
.signature-card strong {{ display: block; font-size: 11px; text-transform: uppercase; }}
.signature-card span {{ display: block; font-size: 11px; font-weight: 700; margin-top: 1px; }}
.footer {{ border-top: 1px solid var(--line); color: var(--muted); margin-top: 18px; padding-top: 10px; }}
@media (max-width: 640px) {{ .grid, .signature-grid {{ grid-template-columns: 1fr; }} }}
@media print {{ body {{ padding: 0; }} .sheet {{ border: 0; max-width: none; }} .no-print {{ display: none !important; }} .signature-panel {{ page-break-inside: avoid; }} }}
</style>
</head>
<body>
<div class="sheet">
  <div class="topbar">
    <img src="/MUFFIN_ICONO.jpg" alt="{e(INSTITUTION_NAME)}">
    <div class="brand">
      <h1>{e(INSTITUTION_NAME)}</h1>
      <p>MUFFIN - Reporte de resultados microbiológicos</p>
    </div>
    <div class="actions no-print"><button onclick="window.print()">Imprimir / guardar PDF</button></div>
  </div>
  {final_notice}
  <div class="grid">
    <div class="field"><strong>Orden</strong>{e(order_info.get('orden_numero') or order.get('order_number'))}</div>
    <div class="field"><strong>Fecha de orden</strong>{e(order_info.get('orden_fecha') or local_datetime_value(order.get('ordered_at'))[:10])}</div>
    <div class="field"><strong>Estado</strong>{e(status_label)}</div>
    <div class="field"><strong>HC</strong>{e(patient.get('persona_hc'))}</div>
    <div class="field"><strong>Paciente</strong>{e((patient.get('persona_apellidos') or '') + ', ' + (patient.get('persona_nombres') or ''))}</div>
    <div class="field"><strong>Edad / género</strong>{e(patient.get('persona_edad'))} / {e(patient.get('persona_genero'))}</div>
    <div class="field"><strong>Procedencia</strong>{e((order_info.get('oMic_procedencia') or {}).get('procedencia_desc'))}</div>
    <div class="field"><strong>Servicio</strong>{e((order_info.get('oMic_servicio') or {}).get('servicio_desc'))}</div>
    <div class="field"><strong>Médico</strong>{e((clinician.get('medico_apellidos') or '') + ' ' + (clinician.get('medico_nombres') or ''))}</div>
  </div>
  {item_sections}
  {signatures_html}
  <div class="footer">Emitido por MUFFIN el {e(generated_at)}. Verifique identidad del paciente, muestra y estado del resultado antes de la entrega.</div>
</div>
</body>
</html>"""
        self.send_bytes(body.encode("utf-8"), 200, "text/html; charset=utf-8")

    def _send_report_error(self, message: str) -> None:
        body = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Reporte no disponible</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;color:#294c52}}.box{{border:1px solid #d8ebe5;border-radius:8px;padding:18px;max-width:680px}}</style>
</head><body><div class="box"><h1>Reporte no disponible</h1><p>{html.escape(message)}</p></div></body></html>"""
        self.send_bytes(body.encode("utf-8"), 404, "text/html; charset=utf-8")

    def _client_signer_for_user(self, user: dict | None) -> dict | None:
        if not isinstance(user, dict):
            return None
        username = normalize_match_key(user.get("username"))
        full_name = normalize_match_key(f"{user.get('given_name', '')} {user.get('family_name', '')}")
        for signer in CLIENT_SIGNERS:
            usernames = {normalize_match_key(item) for item in signer.get("usernames", ())}
            signer_name = normalize_match_key(signer.get("name"))
            if username and username in usernames:
                return signer
            if signer_name and full_name and (signer_name == full_name or signer_name in full_name):
                return signer
        return None

    def _report_signer(self, token: str, report_items: list[dict]) -> dict | None:
        validator_ids = {
            item.get("result", {}).get("final_by")
            for item in report_items
            if report_status_label(
                item.get("result", {}).get("status") or item.get("translated", {}).get("orden_det_estado"),
                culture_result_code(item.get("result", {})),
            )
            == "FINALIZADO"
            and item.get("result", {}).get("final_by")
        }
        if len(validator_ids) != 1:
            return None
        validator_id = next(iter(validator_ids))
        status, current_user = api_req("GET", "/auth/me", token)
        if status == 200 and isinstance(current_user, dict):
            if current_user.get("id") == validator_id:
                return self._client_signer_for_user(current_user)
        status, users = api_req("GET", "/admin/users", token)
        if status == 200 and isinstance(users, list):
            for user in users:
                if isinstance(user, dict) and user.get("id") == validator_id:
                    return self._client_signer_for_user(user)
        return None

    def _build_report_item(self, token: str, raw_item: dict) -> dict | None:
        item_id = raw_item.get("id", "")
        if not item_id:
            return None
        context = self._result_context(token, item_id=item_id)
        translated = self._translate_result_worklist_item(context) if context else {}
        if not translated:
            translated = {
                "orden_det_id": item_id,
                "orden_det_codebar": raw_item.get("barcode", ""),
                "orden_det_estado": raw_item.get("status", ""),
                "fecha_muestra_toma": local_datetime_value(raw_item.get("collection_at")),
                "fecha_muestra_recepcion": local_datetime_value(raw_item.get("received_at")),
                "oMic_examen": {"examen_desc": raw_item.get("exam_id", "")},
                "oMic_muestra": {"muestra_desc": raw_item.get("specimen_type_id", "")},
                "oMic_orden": {},
            }
        status, result = api_req("GET", f"/order-items/{quote(item_id, safe='')}/result", token)
        if status != 200 or not isinstance(result, dict):
            result = {"values": [], "status": translated.get("orden_det_estado", "")}

        organisms = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/organisms")}
        antibiotics = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/antibiotics")}
        colony_counts = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/colony-count-options")}
        isolates = []
        result_id = result.get("id")
        if result_id:
            isolate_status, isolate_rows = api_req("GET", f"/results/{quote(result_id, safe='')}/isolates", token)
            if isolate_status == 200 and isinstance(isolate_rows, list):
                for isolate in isolate_rows:
                    ast_status, ast_rows = api_req("GET", f"/isolates/{quote(isolate.get('id', ''), safe='')}/antimicrobial-results", token)
                    isolates.append(
                        {
                            "isolate": isolate,
                            "organism": organisms.get(isolate.get("organism_id"), {}),
                            "colony_count": colony_counts.get(isolate.get("colony_count_option_id"), {}),
                            "ast_rows": ast_rows if ast_status == 200 and isinstance(ast_rows, list) else [],
                            "antibiotics": antibiotics,
                        }
                    )
        return {"translated": translated, "result": result, "isolates": isolates}

    def _render_report_item(self, report_item: dict) -> str:
        translated = report_item["translated"]
        result = report_item["result"]
        exam = translated.get("oMic_examen", {})
        specimen = translated.get("oMic_muestra", {})

        def e(value: object) -> str:
            return html.escape(str(value or ""))

        def display_value(parameter: dict) -> str:
            value_code = parameter.get("value_code")
            if value_code:
                options = dict(select_options_from_schema(parameter.get("options_schema")))
                return str(options.get(str(value_code), value_code))
            return str(parameter.get("value_text") or "")

        parameter_rows = []
        for parameter in sorted(result.get("values", []), key=lambda row: row.get("display_order") or 0):
            if parameter.get("code") in SUPPRESSED_RESULT_PARAMETERS:
                continue
            value = display_value(parameter)
            if not value:
                continue
            parameter_rows.append(
                f"<tr><td>{e(uppercase_report_value(parameter.get('name')))}</td>"
                f"<td>{e(uppercase_report_value(value))}</td>"
                f"<td>{e(report_parameter_method_label(parameter.get('code'), parameter.get('methodology')))}</td></tr>"
            )
        parameters_html = (
            "<table><thead><tr><th>Parámetro</th><th>Resultado</th><th>Método</th></tr></thead><tbody>"
            + "".join(parameter_rows)
            + "</tbody></table>"
            if parameter_rows
            else "<div class='empty'>Sin parámetros informados.</div>"
        )

        isolate_sections = []
        for isolate_data in report_item["isolates"]:
            isolate = isolate_data["isolate"]
            organism = isolate_data["organism"]
            colony_count = isolate_data["colony_count"]
            ast_rows = []
            antibiotics = isolate_data["antibiotics"]
            for row in isolate_data["ast_rows"]:
                if not row.get("is_reportable", True):
                    continue
                antibiotic = antibiotics.get(row.get("antibiotic_id"), {})
                interpretation = {"POS": "+", "NEG": "-"}.get(row.get("interpretation"), row.get("interpretation", ""))
                ast_rows.append(
                    f"<tr><td>{e(uppercase_report_value(antibiotic.get('name') or row.get('antibiotic_id')))}</td>"
                    f"<td>{e(report_ast_value(row.get('method'), row.get('mic_value')))}</td>"
                    f"<td>{e(uppercase_report_value(interpretation))}</td><td>{e(report_ast_method_label(row.get('method')))}</td></tr>"
                )
            ast_html = (
                "<table><thead><tr><th>Antibiótico</th><th>Valor</th><th>Interpretación</th><th>Método</th></tr></thead><tbody>"
                + "".join(ast_rows)
                + "</tbody></table>"
                if ast_rows
                else "<div class='empty'>Sin antibiograma reportable.</div>"
            )
            isolate_sections.append(
                f"<h3>Aislado: {e(uppercase_report_value(organism.get('name') or isolate.get('organism_id')))}</h3>"
                f"<div class='grid'><div class='field'><strong>Recuento</strong>{e(uppercase_report_value(colony_count.get('name') or isolate.get('colony_count_option_id')))}</div>"
                f"<div class='field'><strong>Fenotipo</strong>{e(uppercase_report_value(isolate.get('phenotype')))}</div>"
                f"<div class='field'><strong>Comentario</strong>{e(uppercase_report_value(isolate.get('comment')))}</div></div>"
                f"{ast_html}"
            )

        isolates_html = "".join(isolate_sections) if isolate_sections else "<div class='empty'>Sin identificación/antibiograma registrado.</div>"
        item_status = report_status_label(result.get("status") or translated.get("orden_det_estado"), culture_result_code(result))
        return f"""
<h2>{e(uppercase_report_value(exam.get('examen_desc')))}</h2>
<div class="grid">
  <div class="field"><strong>Muestra</strong>{e(uppercase_report_value(specimen.get('muestra_desc')))}</div>
  <div class="field"><strong>Código de barras</strong>{e(translated.get('orden_det_codebar'))}</div>
  <div class="field"><strong>Estado</strong>{e(item_status)}</div>
  <div class="field"><strong>Toma</strong>{e(translated.get('fecha_muestra_toma'))}</div>
  <div class="field"><strong>Recepción</strong>{e(translated.get('fecha_muestra_recepcion'))}</div>
  <div class="field"><strong>Guardado</strong>{e(local_datetime_value(result.get('saved_at')))}</div>
</div>
{parameters_html}
{isolates_html}
"""

    # ── AST PANEL HANDLERS (microbiology) ──

    def _catalog_items(self, token: str, api_path: str) -> list[dict]:
        page_size = 3000 if api_path == "/catalogs/organisms" else 100
        status, page = api_req("GET", f"{api_path}?page_size={page_size}", token)
        if status == 200 and isinstance(page, dict):
            return page.get("data", [])
        return page if status == 200 and isinstance(page, list) else []

    def _resolve_catalog_id(self, token: str, api_path: str, value: str) -> str:
        normalized = str(value or "").strip().casefold()
        if not normalized:
            return ""
        for item in self._catalog_items(token, api_path):
            candidates = (item.get("id"), item.get("code"), item.get("name"))
            if any(str(candidate or "").casefold() == normalized for candidate in candidates):
                return str(item.get("id", ""))
        return ""

    def _result_context(self, token: str, *, item_id: str = "", barcode: str = "") -> dict | None:
        if item_id:
            status, rows = api_req("GET", f"/result-worklist?item_id={quote(item_id, safe='')}", token)
        elif barcode:
            status, rows = api_req("GET", f"/result-worklist?search={quote(barcode, safe='')}", token)
        else:
            return None
        if status != 200 or not isinstance(rows, list):
            return None
        if item_id:
            return next((row for row in rows if (row.get("item") or {}).get("id") == item_id), None)
        return next((row for row in rows if (row.get("item") or {}).get("barcode") == barcode), None)

    def _ensure_result(self, token: str, item_id: str) -> dict | None:
        status, result = api_req("GET", f"/order-items/{item_id}/result", token)
        if status != 200 or not isinstance(result, dict):
            return None
        if result.get("id"):
            return result
        values = []
        for parameter in result.get("values", []):
            value = {"parameter_definition_id": parameter.get("parameter_definition_id", "")}
            if parameter.get("value_code") is not None:
                value["value_code"] = parameter["value_code"]
            elif parameter.get("value_text") is not None:
                value["value_text"] = parameter["value_text"]
            if parameter.get("observed_at") is not None:
                value["observed_at"] = parameter["observed_at"]
            values.append(value)
        status, result = api_req(
            "PUT",
            f"/order-items/{item_id}/result",
            token,
            {"values": values, "ready_for_validation": False},
        )
        return result if status == 200 and isinstance(result, dict) else None

    def _proxy_ast_panel_register(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        item_id = obj.get("item_id", obj.get("detalle_id", ""))
        barcode = obj.get("respanel_codebar", "")
        if not item_id:
            context = self._result_context(token, barcode=barcode)
            item_id = ((context or {}).get("item") or {}).get("id", "")
        organism_id = obj.get("organismo_id", obj.get("organism_id", obj.get("respanel_organismo_cod", "")))
        panel_id = obj.get("panel_id", obj.get("temporal1", ""))
        organism_id = self._resolve_catalog_id(token, "/catalogs/organisms", organism_id)
        panel_id = self._resolve_catalog_id(token, "/catalogs/ast-panels", panel_id) if panel_id else ""
        if not item_id or not organism_id:
            self.send_json({"resultado": False, "mensaje": "item_id y organismo_id requeridos"})
            return
        result = self._ensure_result(token, item_id)
        if not result or not result.get("id"):
            self.send_json({"resultado": False, "mensaje": "No se pudo iniciar el resultado de microbiologia"})
            return
        payload = {"organism_id": organism_id}
        if panel_id:
            payload["ast_panel_id"] = panel_id
        status, data = api_req("POST", f"/results/{result['id']}/isolates", token, payload)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Panel AST registrado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_panel_delete(self, token: str) -> None:
        request_path = self.path if hasattr(self, "path") else ""
        item_id = self._extract_query_param(request_path, "item_id") or self._extract_query_param(request_path, "orden_det_id")
        isolate_id = self._extract_query_param(request_path, "respanel_id") or self._extract_query_param(request_path, "isolate_id")
        if not item_id or not isolate_id:
            self.send_json({"resultado": False, "mensaje": "item_id y aislado_id requeridos"})
            return
        result = self._ensure_result(token, item_id)
        if not result or not result.get("id"):
            self.send_json({"resultado": False, "mensaje": "resultado_id requerido"})
            return
        status, data = api_req("DELETE", f"/results/{result['id']}/isolates/{isolate_id}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Aislado eliminado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_panel_by_codebar(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        barcode = self._extract_query_param(request_path, "codebar")
        context = self._result_context(token, barcode=barcode)
        result = (context or {}).get("result") or {}
        if not result.get("id"):
            self.send_json({"data": [], "resultado": True})
            return
        status, isolates = api_req("GET", f"/results/{result['id']}/isolates", token)
        organisms = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/organisms")}
        if status == 200 and isinstance(isolates, list):
            translated = []
            for isolate in isolates:
                organism = organisms.get(isolate.get("organism_id"), {})
                translated.append(
                    {
                        "respanel_id": isolate.get("id", ""),
                        "respanel_organismo_cod": isolate.get("id", ""),
                        "respanel_organismo_desc": organism.get("name", isolate.get("organism_id", "")),
                    }
                )
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudieron cargar los aislados"})

    def _proxy_ast_panel_by_org(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        barcode = self._extract_query_param(request_path, "codebar")
        isolate_id = self._extract_query_param(request_path, "organismo_cod")
        context = self._result_context(token, barcode=barcode)
        result = (context or {}).get("result") or {}
        if not result.get("id") or not isolate_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, isolate = api_req("GET", f"/results/{result['id']}/isolates/{isolate_id}", token)
        if status != 200 or not isinstance(isolate, dict):
            self.send_json({"data": [], "resultado": True})
            return
        organisms = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/organisms")}
        organism = organisms.get(isolate.get("organism_id"), {})
        self.send_json(
            {
                "data": [
                    {
                        "respanel_id": isolate.get("id", ""),
                        "respanel_organismo_cod": isolate.get("id", ""),
                        "respanel_organismo_desc": organism.get("name", isolate.get("organism_id", "")),
                        "respanel_recuento": isolate.get("colony_count_option_id") or "",
                        "respanel_organismo_fenotipo": isolate.get("phenotype") or "",
                        "respanel_organismo_comentario": isolate.get("comment") or "",
                    }
                ],
                "resultado": True,
            }
        )

    def _proxy_ast_detail_save(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        panel = obj.get("oMic_res_panel") or {}
        item_id = ((panel.get("oMic_orden_detalle") or {}).get("orden_det_id", ""))
        isolate_id = panel.get("respanel_id", obj.get("aislado_id", obj.get("isolate_id", "")))
        result = self._ensure_result(token, item_id) if item_id else None
        if not isolate_id or not result or not result.get("id"):
            self.send_json({"resultado": False, "mensaje": "aislado_id y resultado_id requeridos"})
            return

        isolate_payload = {
            "colony_count_option_id": panel.get("respanel_recuento") or None,
            "phenotype": panel.get("respanel_organismo_fenotipo") or None,
            "comment": panel.get("respanel_organismo_comentario") or None,
        }
        status, data = api_req(
            "PATCH",
            f"/results/{result['id']}/isolates/{isolate_id}",
            token,
            isolate_payload,
        )
        if status != 200:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or "No se pudo actualizar el aislado"})
            return

        def values(key: str) -> list[str]:
            parts = str(obj.get(key, "")).split("|")
            return parts[:-1] if parts and parts[-1] == "" else parts

        antibiotic_ids = values("respaneldet_anti_cod_all")
        mic_values = values("respaneldet_anti_cmi_all")
        interpretations = values("respaneldet_anti_inter_all")
        not_reportable = values("respaneldet_anti_estado_all")
        methods = values("respaneldet_anti_metodologia_all")
        existing_status, existing_rows = api_req("GET", f"/isolates/{isolate_id}/antimicrobial-results", token)
        if existing_status != 200 or not isinstance(existing_rows, list):
            self.send_json({"resultado": False, "mensaje": "No se pudo cargar el antibiograma"})
            return
        existing = {row.get("antibiotic_id"): row for row in existing_rows}
        for index, antibiotic_id in enumerate(antibiotic_ids):
            if not antibiotic_id:
                continue
            interpretation = interpretations[index] if index < len(interpretations) else "NA"
            interpretation = {"+": "POS", "-": "NEG"}.get(interpretation, interpretation or "NA")
            method = editor_ast_method(methods[index] if index < len(methods) else "")
            mic_value = mic_values[index].strip() if index < len(mic_values) else ""
            payload = {
                "mic_value": mic_value if method == "CMI" and mic_value != "-" else None,
                "interpretation": interpretation,
                "method": method,
                "is_reportable": not (
                    index < len(not_reportable) and not_reportable[index].lower() == "true"
                ),
            }
            current = existing.get(antibiotic_id)
            if current:
                status, data = api_req(
                    "PATCH",
                    f"/isolates/{isolate_id}/antimicrobial-results/{current['id']}",
                    token,
                    payload,
                )
            else:
                status, data = api_req(
                    "POST",
                    f"/isolates/{isolate_id}/antimicrobial-results",
                    token,
                    {"antibiotic_id": antibiotic_id} | payload,
                )
            if status not in (200, 201):
                self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or "No se pudo guardar el antibiograma"})
                return
        self.send_json({"resultado": True, "mensaje": "Identificacion y antibiograma guardados"})

    def _proxy_ast_detail_manual(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        panel = obj.get("oMic_res_panel") or {}
        isolate_id = obj.get("isolate_id", panel.get("respanel_id", ""))
        antibiotic_id = obj.get("antibiotic_id", obj.get("respaneldet_anti_cod", ""))
        antibiotic_id = self._resolve_catalog_id(token, "/catalogs/antibiotics", antibiotic_id)
        interpretation = obj.get("interpretation", obj.get("respaneldet_anti_inter", "NA"))
        interpretation = {"+": "POS", "-": "NEG"}.get(interpretation, interpretation)
        if not isolate_id or not antibiotic_id:
            self.send_json({"resultado": False, "mensaje": "Aislado y antibiotico requeridos"})
            return
        payload = {
            "antibiotic_id": antibiotic_id,
            "mic_value": None,
            "interpretation": interpretation,
            "method": "DISCO",
            "is_reportable": True,
        }
        status, data = api_req("POST", f"/isolates/{isolate_id}/antimicrobial-results", token, payload)
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Antibiotico agregado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_detail_by_org(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        isolate_id = self._extract_query_param(request_path, "organismo_cod")
        if not isolate_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, rows = api_req("GET", f"/isolates/{isolate_id}/antimicrobial-results", token)
        antibiotics = {item.get("id"): item for item in self._catalog_items(token, "/catalogs/antibiotics")}
        if status == 200 and isinstance(rows, list):
            translated = []
            for row in rows:
                antibiotic = antibiotics.get(row.get("antibiotic_id"), {})
                interpretation = {"POS": "+", "NEG": "-"}.get(row.get("interpretation"), row.get("interpretation", "NA"))
                method = editor_ast_method(row.get("method"))
                translated.append(
                    {
                        "respaneldet_id": row.get("id", ""),
                        "respaneldet_anti_cod": row.get("antibiotic_id", ""),
                        "respaneldet_anti_desc": uppercase_report_value(antibiotic.get("name", row.get("antibiotic_id", ""))),
                        "respaneldet_anti_cmi": (row.get("mic_value") or "") if method == "CMI" else "-",
                        "respaneldet_anti_inter": interpretation,
                        "respaneldet_anti_estado": not row.get("is_reportable", True),
                        "respaneldet_anti_metodologia": method,
                        "respaneldet_anti_macanismo": 0,
                    }
                )
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": False, "mensaje": "No se pudo cargar el antibiograma"})

    # ── AST PANEL CATALOG HANDLERS ──

    def _proxy_ast_panel_create(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        code = obj.get("code", obj.get("orga_panel_id", ""))
        name = obj.get("name", obj.get("orga_panel_desc", ""))
        if not code or not name:
            self.send_json({"resultado": False, "mensaje": "code y name requeridos"})
            return
        status, data = api_req("POST", "/catalogs/ast-panels", token, {"code": code, "name": name})
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Panel AST creado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_panel_delete_api(self, token: str, path: str) -> None:
        body = self._read_body()
        panel_id = (body or {}).get("panel_id", "") or (body or {}).get("orga_panel_id", "")
        if not panel_id:
            self.send_json({"resultado": False, "mensaje": "panel_id requerido"})
            return
        status, data = api_req("DELETE", f"/catalogs/ast-panels/{panel_id}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Panel AST eliminado"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_panel_antibiotics(self, token: str, path: str) -> None:
        panel_id = self._extract_query_param(path, "panel_id") or self._extract_query_param(path, "orga_panel_id")
        if not panel_id:
            self.send_json({"data": [], "resultado": True})
            return
        status, data = api_req("GET", f"/catalogs/ast-panels/{panel_id}/antibiotics", token)
        if status == 200 and isinstance(data, list):
            translated = [{"atb_id": a.get("antibiotic_id", ""), "atb_desc": a.get("name", ""), "atb_orden": a.get("sort_order", 0)} for a in data]
            self.send_json({"data": translated, "resultado": True})
        else:
            self.send_json({"data": [], "resultado": True})

    def _proxy_ast_panel_antibiotic_add(self, token: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        panel_id = obj.get("panel_id", obj.get("orga_panel_id", ""))
        atb_id = obj.get("atb_id", obj.get("antibiotic_id", ""))
        if not panel_id or not atb_id:
            self.send_json({"resultado": False, "mensaje": "panel_id y atb_id requeridos"})
            return
        status, data = api_req("PUT", f"/catalogs/ast-panels/{panel_id}/antibiotics/{atb_id}", token, {"sort_order": obj.get("atb_orden", 0)})
        if status in (200, 201):
            self.send_json({"resultado": True, "mensaje": "Antibiotico agregado al panel"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    def _proxy_ast_panel_antibiotic_remove(self, token: str, path: str) -> None:
        body = self._read_body()
        obj = (body or {}).get("objeto", body or {})
        panel_id = obj.get("panel_id", obj.get("orga_panel_id", ""))
        atb_id = obj.get("atb_id", obj.get("antibiotic_id", ""))
        if not panel_id or not atb_id:
            self.send_json({"resultado": False, "mensaje": "panel_id y atb_id requeridos"})
            return
        status, data = api_req("DELETE", f"/catalogs/ast-panels/{panel_id}/antibiotics/{atb_id}", token)
        if status in (200, 204):
            self.send_json({"resultado": True, "mensaje": "Antibiotico eliminado del panel"})
        else:
            self.send_json({"resultado": False, "mensaje": self._api_error(status, data) or f"Error HTTP {status}"})

    # ── EXPORT / REPORT HANDLERS ──

    def _selected_id_set(self, raw: str) -> set[str]:
        cleaned = raw.strip()
        if not cleaned or cleaned.upper() == "ALL":
            return set()
        return {item.strip().strip("'\"") for item in cleaned.split(",") if item.strip().strip("'\"")}

    def _worklist_rows_for_path(self, token: str, path: str) -> list[dict]:
        request_path = self.path if hasattr(self, "path") else path
        date_from = self._extract_query_param(request_path, "orden_fecha_ini")
        date_to = self._extract_query_param(request_path, "orden_fecha_fin")
        search = self._extract_query_param(request_path, "orden_buscar")
        query = []
        if date_from:
            query.append(f"from={quote(date_from, safe='')}")
        if date_to:
            query.append(f"to={quote(date_to, safe='')}")
        if search:
            query.append(f"search={quote(search, safe='')}")
        status, rows = api_req("GET", f"/result-worklist?{'&'.join(query)}", token)
        return rows if status == 200 and isinstance(rows, list) else []

    def _send_export_table(self, title: str, columns: list[str], rows: list[list[object]]) -> None:
        def e(value: object) -> str:
            return html.escape(str(value or ""))

        body_rows = "".join("<tr>" + "".join(f"<td>{e(value)}</td>" for value in row) + "</tr>" for row in rows)
        empty = "<tr><td colspan='%d' class='empty'>Sin datos para el rango seleccionado.</td></tr>" % max(len(columns), 1)
        page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} - MUFFIN</title>
<style>
body{{color:#1f3438;font-family:Arial,Helvetica,sans-serif;font-size:12px;margin:0;padding:22px}}
.top{{align-items:center;border-bottom:3px solid #167d86;display:flex;gap:12px;margin-bottom:16px;padding-bottom:10px}}
.top img{{border-radius:50%;height:44px;width:44px}}h1{{font-size:18px;margin:0}}p{{color:#607477;margin:2px 0 0}}
button{{background:#167d86;border:0;border-radius:5px;color:white;font-weight:700;margin-left:auto;padding:8px 12px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #b9cdca;padding:6px 7px;text-align:left;vertical-align:top}}
th{{background:#eef6f3;font-size:10px;text-transform:uppercase}}.empty{{color:#607477;font-style:italic;text-align:center}}
@media print{{body{{padding:0}}button{{display:none}}}}
</style>
</head>
<body>
<div class="top"><img src="/MUFFIN_ICONO.jpg" alt="MUFFIN"><div><h1>{e(title)}</h1><p>{e(INSTITUTION_NAME)} · Generado {e(datetime.now(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M'))}</p></div><button onclick="window.print()">Imprimir / guardar PDF</button></div>
<table><thead><tr>{''.join(f'<th>{e(col)}</th>' for col in columns)}</tr></thead><tbody>{body_rows or empty}</tbody></table>
</body>
</html>"""
        self.send_bytes(page.encode("utf-8"), 200, "text/html; charset=utf-8", cache_control="no-store")

    def _proxy_production_report_export(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        exam_ids = self._selected_id_set(self._extract_query_param(request_path, "examen_id"))
        result_filter = (self._extract_query_param(request_path, "orden_filtro") or "ALL").upper()
        rows = []
        for row in self._worklist_rows_for_path(token, request_path):
            item = row.get("item") or {}
            order = row.get("order") or {}
            patient = row.get("patient") or {}
            exam = row.get("exam") or {}
            origin = row.get("origin") or {}
            service = row.get("service") or {}
            result = row.get("result") or {}
            if exam_ids and exam.get("id") not in exam_ids:
                continue
            if result_filter not in {"ALL", "0"} and str(result.get("status") or item.get("status") or "").upper() != result_filter:
                continue
            rows.append(
                [
                    str(order.get("ordered_at", ""))[:10],
                    order.get("order_number", ""),
                    patient.get("medical_record_number", ""),
                    f"{patient.get('family_name', '')}, {patient.get('given_name', '')}",
                    exam.get("name", ""),
                    origin.get("name", ""),
                    service.get("name", ""),
                    report_status_label(result.get("status") or item.get("status")),
                ]
            )
        self._send_export_table("Reporte de produccion microbiologica", ["Fecha", "Orden", "HC", "Paciente", "Examen", "Procedencia", "Servicio", "Estado"], rows)

    def _proxy_worksheet_report_export(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        section_id = self._extract_query_param(request_path, "seccion_id")
        section_name = self._extract_query_param(request_path, "seccion_nombre") or "Microbiologia"
        rows = []
        for row in self._worklist_rows_for_path(token, request_path):
            item = row.get("item") or {}
            order = row.get("order") or {}
            patient = row.get("patient") or {}
            exam = row.get("exam") or {}
            specimen = row.get("specimen") or {}
            if section_id and exam.get("laboratory_area_id") != section_id:
                continue
            rows.append(
                [
                    str(order.get("ordered_at", ""))[:10],
                    order.get("order_number", ""),
                    item.get("barcode", ""),
                    patient.get("medical_record_number", ""),
                    f"{patient.get('family_name', '')}, {patient.get('given_name', '')}",
                    exam.get("name", ""),
                    specimen.get("name", ""),
                    item.get("status", ""),
                ]
            )
        self._send_export_table(f"Hoja de trabajo - {section_name}", ["Fecha", "Orden", "Codigo barras", "HC", "Paciente", "Examen", "Muestra", "Estado"], rows)

    def _proxy_idt_ast_report_export(self, token: str, path: str) -> None:
        request_path = self.path if hasattr(self, "path") else path
        organism_ids = self._selected_id_set(self._extract_query_param(request_path, "orga_id"))
        antibiotic_ids = self._selected_id_set(self._extract_query_param(request_path, "atb_id"))
        rows = []
        for row in self._worklist_rows_for_path(token, request_path):
            item = row.get("item") or {}
            order = row.get("order") or {}
            patient = row.get("patient") or {}
            result_status, result = api_req("GET", f"/order-items/{quote(item.get('id', ''), safe='')}/result", token)
            if result_status != 200 or not isinstance(result, dict) or not result.get("id"):
                continue
            isolate_status, isolates = api_req("GET", f"/results/{quote(result['id'], safe='')}/isolates", token)
            if isolate_status != 200 or not isinstance(isolates, list):
                continue
            for isolate in isolates:
                if organism_ids and isolate.get("organism_id") not in organism_ids:
                    continue
                organism = isolate.get("organism") or {}
                ast_status, ast_rows = api_req("GET", f"/isolates/{quote(isolate.get('id', ''), safe='')}/antimicrobial-results", token)
                if ast_status != 200 or not isinstance(ast_rows, list):
                    continue
                for ast_row in ast_rows:
                    if antibiotic_ids and ast_row.get("antibiotic_id") not in antibiotic_ids:
                        continue
                    if not ast_row.get("is_reportable", True):
                        continue
                    antibiotic = ast_row.get("antibiotic") or {}
                    rows.append(
                        [
                            str(order.get("ordered_at", ""))[:10],
                            order.get("order_number", ""),
                            patient.get("medical_record_number", ""),
                            f"{patient.get('family_name', '')}, {patient.get('given_name', '')}",
                            organism.get("name") or isolate.get("organism_id", ""),
                            antibiotic.get("name") or ast_row.get("antibiotic_id", ""),
                            ast_row.get("interpretation", ""),
                            report_ast_method_label(ast_row.get("method")),
                        ]
                    )
        self._send_export_table("Reporte de identificacion y antibiograma", ["Fecha", "Orden", "HC", "Paciente", "Microorganismo", "Antibiotico", "Interpretacion", "Metodo"], rows)

    def _proxy_patient_export(self, token: str) -> None:
        status, data = api_req("GET", "/patients?page_size=100", token)
        patients = data.get("data", []) if status == 200 and isinstance(data, dict) else []
        rows = [
            [patient.get("medical_record_number", ""), patient.get("family_name", ""), patient.get("given_name", ""), patient.get("sex", ""), patient.get("birth_date", "")]
            for patient in patients
        ]
        self._send_export_table("Exportacion de pacientes", ["HC", "Apellidos", "Nombres", "Sexo", "Fecha nacimiento"], rows)

    # ── HELPERS ──

    def _send_html_message(self, title: str, message: str, status: int = 200) -> None:
        page = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>body{{color:#294c52;font-family:Arial,sans-serif;margin:32px}}.box{{border:1px solid #d8ebe5;border-radius:8px;max-width:680px;padding:18px}}</style>
</head><body><div class="box"><h1>{html.escape(title)}</h1><p>{html.escape(message)}</p></div></body></html>"""
        self.send_bytes(page.encode("utf-8"), status, "text/html; charset=utf-8", cache_control="no-store")

    def _extract_query_param(self, path: str, param: str) -> str:
        if "?" in path:
            for pair in path.split("?", 1)[1].split("&"):
                if pair.startswith(param + "="):
                    return unquote(pair.split("=", 1)[1])
        return ""


def main() -> None:
    Handler.manifest = load_manifest()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"MUFFIN frontend corriendo en http://{HOST}:{PORT}/MUFFIN/")
    print(f"Mirror: {MIRROR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
