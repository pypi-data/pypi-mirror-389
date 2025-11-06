from __future__ import annotations
import secrets
import logging
import re
import json
import hashlib
import time
from typing import List, Dict, Any
from urllib.parse import urlparse

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache  # Para fingerprinting básico


# ==========================================================
# CONFIGURACIÓN DE LOGGING
# ==========================================================
logger = logging.getLogger("csrfdefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


# ==========================================================
# CONSTANTES Y PATRONES
# ==========================================================
STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_HEADER_NAMES = ("HTTP_X_CSRFTOKEN", "HTTP_X_CSRF_TOKEN")
CSRF_COOKIE_NAME = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
POST_FIELD_NAME = "csrfmiddlewaretoken"

# Content-Type sospechoso
SUSPICIOUS_CT_PATTERNS = [
    re.compile(r"text/plain", re.I),
    re.compile(r"application/x-www-form-urlencoded", re.I),
    re.compile(r"multipart/form-data", re.I),
    re.compile(r"application/json", re.I),
    re.compile(r"text/html", re.I),  # Para HTML CSRF
]

# Parámetros sensibles
SENSITIVE_PARAMS = [
    "password", "csrfmiddlewaretoken", "token", "amount",
    "transfer", "delete", "update", "action", "email", "username"
]

# Campos sensibles analizados sin descuento
SENSITIVE_FIELDS = ["password", "csrfmiddlewaretoken", "token", "auth", "email", "username"]

# Umbrales y configuraciones
CSRF_DEFENSE_MIN_SIGNALS = getattr(settings, "CSRF_DEFENSE_MIN_SIGNALS", 1)
CSRF_DEFENSE_EXCLUDED_API_PREFIXES = getattr(settings, "CSRF_DEFENSE_EXCLUDED_API_PREFIXES", ["/api/"])
HIGH_THRESHOLD = getattr(settings, "CSRF_DEFENSE_HIGH_SCORE", 3.0)
MED_THRESHOLD = getattr(settings, "CSRF_DEFENSE_MED_SCORE", 2.0)
LOW_THRESHOLD = getattr(settings, "CSRF_DEFENSE_LOW_SCORE", 0.5)

# Patrones de payload sospechosos
CSRF_PAYLOAD_PATTERNS = [
    (re.compile(r"<script[^>]*>.*?</script>", re.I | re.S), "Script tag en payload", 0.9),
    (re.compile(r"javascript\s*:", re.I), "URI javascript: en payload", 0.8),
    (re.compile(r"http[s]?://[^\s]+", re.I), "URL externa en payload", 0.7),
    (re.compile(r"eval\s*\(", re.I), "eval() en payload", 1.0),
    (re.compile(r"document\.cookie", re.I), "Acceso a cookie en payload", 0.9),
    (re.compile(r"innerHTML\s*=", re.I), "Manipulación DOM innerHTML", 0.8),
    (re.compile(r"XMLHttpRequest", re.I), "XHR en payload", 0.7),
    (re.compile(r"fetch\s*\(", re.I), "fetch() en payload", 0.7),
    (re.compile(r"&#x[0-9a-fA-F]+;", re.I), "Entidades HTML en payload", 0.6),
    (re.compile(r"%3Cscript", re.I), "Script URL-encoded en payload", 0.8),
    (re.compile(r"on\w+\s*=", re.I), "Eventos on* en payload", 0.7),
    (re.compile(r"alert\s*\(", re.I), "alert() en payload (prueba)", 0.5),
]


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[0]
    return request.META.get("REMOTE_ADDR", "")


def host_from_header(header_value: str) -> str | None:
    if not header_value:
        return None
    try:
        parsed = urlparse(header_value)
        if parsed.netloc:
            return parsed.netloc.split(":")[0]
        return header_value.split(":")[0]
    except Exception:
        return None


def origin_matches_host(request) -> bool:
    host_header = request.META.get("HTTP_HOST") or request.META.get("SERVER_NAME")
    if not host_header:
        return True

    host = host_header.split(":")[0]
    origin = request.META.get("HTTP_ORIGIN", "")
    referer = request.META.get("HTTP_REFERER", "")

    # Bloquear obvious javascript: referers
    if any(re.search(r"(javascript:|<script|data:text/html)", h or "", re.I) for h in [origin, referer]):
        return False

    if origin_host := host_from_header(origin):
        if origin_host == host:
            return True
    if referer_host := host_from_header(referer):
        if referer_host == host:
            return True

    if not origin and not referer:
        return True

    return False


def has_csrf_token(request) -> bool:
    for h in CSRF_HEADER_NAMES:
        if request.META.get(h):
            return True
    if request.COOKIES.get(CSRF_COOKIE_NAME):
        return True
    try:
        if request.method == "POST" and hasattr(request, "POST"):
            if request.POST.get(POST_FIELD_NAME):
                return True
    except Exception:
        pass
    return False


def extract_payload_text(request) -> str:
    parts: List[str] = []
    try:
        body = request.body.decode("utf-8", errors="ignore")
        if body:
            parts.append(body)
    except Exception:
        pass
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        parts.append(qs)
    parts.append(request.META.get("HTTP_USER_AGENT", ""))
    parts.append(request.META.get("HTTP_REFERER", ""))
    return " ".join([p for p in parts if p])


def extract_parameters(request) -> List[str]:
    params = []
    if hasattr(request, "POST"):
        params.extend(request.POST.keys())
    if hasattr(request, "GET"):
        params.extend(request.GET.keys())
    try:
        if request.body and "application/json" in (request.META.get("CONTENT_TYPE") or ""):
            data = json.loads(request.body)
            params.extend(data.keys())
    except Exception:
        pass
    return params


def analyze_payload(value: str) -> float:
    """Analiza payload completo (incluyendo sensibles)."""
    score = 0.0
    for patt, desc, weight in CSRF_PAYLOAD_PATTERNS:
        if patt.search(value):
            score += weight
    return round(score, 3)


def analyze_query_string(request) -> float:
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        return analyze_payload(qs)
    return 0.0


def analyze_headers(request) -> List[str]:
    issues = []
    ua = request.META.get("HTTP_USER_AGENT", "")
    if re.search(r"(script|<|eval|bot|crawler)", ua, re.I):
        issues.append("User-Agent sospechoso (posible automatización/bot)")

    accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    if not accept_lang or len(accept_lang) < 2:
        issues.append("Accept-Language ausente o muy corto (posible bot)")

    return issues


def payload_fingerprint(payload_summary: List[Dict[str, Any]]) -> str | None:
    """Genera huella SHA256 del payload para detectar repetición."""
    if not payload_summary:
        return None
    try:
        parts = [f"{item.get('field','')}:{item.get('snippet','')[:50]}" for item in payload_summary]
        raw = "||".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception:
        return None


# ==========================================================
# MIDDLEWARE PRINCIPAL: CSRFDefenseMiddleware
# ==========================================================
class CSRFDefenseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Saltar paths excluidos
        for prefix in CSRF_DEFENSE_EXCLUDED_API_PREFIXES:
            if request.path.startswith(prefix):
                logger.debug(f"[CSRFDefense] Skip analysis for API prefix {prefix} path {request.path}")
                return None

        client_ip = get_client_ip(request)
        trusted_ips = getattr(settings, "CSRF_DEFENSE_TRUSTED_IPS", [])
        if client_ip in trusted_ips:
            return None

        excluded_paths = getattr(settings, "CSRF_DEFENSE_EXCLUDED_PATHS", [])
        if any(request.path.startswith(p) for p in excluded_paths):
            return None

        method = (request.method or "").upper()
        if method not in STATE_CHANGING_METHODS:
            return None

        descripcion: List[str] = []
        payload = extract_payload_text(request)
        params = extract_parameters(request)

        # 1. Falta token CSRF
        if not has_csrf_token(request):
            descripcion.append("Falta token CSRF en cookie/header/form")

        # 2. Origin/Referer inválido
        if not origin_matches_host(request):
            descripcion.append("Origin/Referer no coinciden con Host (posible cross-site)")

        # 3. Content-Type sospechoso
        content_type = (request.META.get("CONTENT_TYPE") or "")
        for patt in SUSPICIOUS_CT_PATTERNS:
            if patt.search(content_type):
                descripcion.append(f"Content-Type sospechoso: {content_type}")
                break

        # 4. Referer ausente
        referer = request.META.get("HTTP_REFERER", "")
        if not referer and not any(request.META.get(h) for h in CSRF_HEADER_NAMES):
            descripcion.append("Referer ausente y sin X-CSRFToken")

        # 5. Parámetros sensibles en GET
        for p in params:
            if p.lower() in SENSITIVE_PARAMS and method == "GET":
                descripcion.append(f"Parámetro sensible '{p}' enviado en GET (posible CSRF)")

        # 6. JSON sospechoso externo
        if "application/json" in content_type:
            origin = request.META.get("HTTP_ORIGIN") or ""
            if origin and host_from_header(origin) != (request.META.get("HTTP_HOST") or "").split(":")[0]:
                descripcion.append("JSON POST desde origen externo (posible CSRF)")

        # 7. Análisis de payload (POST y JSON)
        payload_score = 0.0
        payload_summary: List[Dict[str, Any]] = []
        try:
            if hasattr(request, "POST"):
                for key, value in request.POST.items():
                    if isinstance(value, str):
                        score = analyze_payload(value)
                        payload_score += score
                        if score > 0:
                            payload_summary.append({"field": key, "snippet": value[:300], "score": score})

            if "application/json" in content_type:
                data = json.loads(request.body.decode("utf-8") or "{}")
                for key, value in data.items():
                    if isinstance(value, str):
                        score = analyze_payload(value)
                        payload_score += score
                        if score > 0:
                            payload_summary.append({"field": key, "snippet": value[:300], "score": score})
        except Exception as e:
            logger.debug(f"Error analizando payload: {e}")

        if payload_score > 0:
            descripcion.append(f"Payload sospechoso detectado (score total: {payload_score})")

        # 8. Query string
        qs_score = analyze_query_string(request)
        if qs_score > 0:
            descripcion.append(f"Query string sospechosa (score: {qs_score})")
            payload_score += qs_score

        # 9. Headers sospechosos
        header_issues = analyze_headers(request)
        descripcion.extend(header_issues)

        # 10. Fingerprint de payload
        pf = payload_fingerprint(payload_summary)
        if pf:
            repeat_key = f"csrf_repeat:{pf}"
            repeat_count = cache.get(repeat_key, 0) + 1
            cache.set(repeat_key, repeat_count, timeout=3600)  # 1h
            if repeat_count > 3:
                descripcion.append(f"Payload repetido {repeat_count} veces (posible ataque coordinado)")

        # ==========================================================
        # SCORING FINAL Y BLOQUEO
        # ==========================================================
        total_signals = len(descripcion)
        if descripcion and total_signals >= CSRF_DEFENSE_MIN_SIGNALS:
            w_csrf = getattr(settings, "CSRF_DEFENSE_WEIGHT", 0.2)
            s_csrf = w_csrf * total_signals + payload_score

            blocked = s_csrf >= MED_THRESHOLD

            request.csrf_attack_info = {
                "ip": client_ip,
                "tipos": ["CSRF"],
                "descripcion": descripcion,
                "payload": json.dumps(payload_summary, ensure_ascii=False)[:1000],
                "score": s_csrf,
                "blocked": blocked,
            }

            logger.warning(
                "CSRF detectado desde IP %s: %s ; path=%s ; Content-Type=%s ; score=%.2f ; blocked=%s",
                client_ip, descripcion, request.path, content_type, s_csrf, blocked
            )
        else:
            if descripcion:
                logger.debug(f"[CSRFDefense] low-signals ({total_signals}) not marking: {descripcion}")

        return None


"""
CSRF Defense Middleware - Ultra Robusto
=======================================
- Detecta múltiples categorías de CSRF (clásico, login, JSON API, etc.)
- Escanea payloads POST, GET, JSON y headers.
- Analiza TODOS los campos sin descuento (máxima sensibilidad).
- Detección de bots y automatización.
- Detección de payloads repetidos (coordinados).
- Scoring configurable + integración con auditoría.
"""
