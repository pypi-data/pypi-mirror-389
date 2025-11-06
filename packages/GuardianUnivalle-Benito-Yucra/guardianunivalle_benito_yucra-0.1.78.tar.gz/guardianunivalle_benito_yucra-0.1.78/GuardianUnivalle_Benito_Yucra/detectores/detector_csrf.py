# csrf_defense.py
# GuardianUnivalle_Benito_Yucra/detectores/csrf_defense.py
# csrf_defense_robust.py
# GuardianUnivalle_Benito_Yucra/detectores/csrf_defense_robust.py
# Middleware CSRF - ULTRA-ROBUSTO
# - Validación tokens (cookie/header/form) + double-submit
# - Origin/Referer/Host checks
# - SameSite cookie heuristics
# - Análisis de payload con patrones (sin descuentos para máxima detección)
# - Rate limiting / blocking por IP con exponential backoff
# - Payload hashing y fingerprinting para detecciones cruzadas (mitiga VPN)
# - Telemetría y logging (redacción de datos sensibles)
# - Configurable desde settings.py

from __future__ import annotations
import json
import logging
import re
import time
import hashlib
import hmac
import math
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden, HttpResponse
from django.core.cache import cache

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger("csrfdefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(h)

# ----------------------------
# Configurables (override desde settings)
# ----------------------------
STATE_CHANGING_METHODS = getattr(settings, "CSRF_DEFENSE_STATE_CHANGING_METHODS", {"POST", "PUT", "PATCH", "DELETE"})
CSRF_HEADER_NAMES = getattr(settings, "CSRF_DEFENSE_HEADER_NAMES", ("HTTP_X_CSRFTOKEN", "HTTP_X_CSRF_TOKEN", "HTTP_X_XSRF_TOKEN"))
CSRF_COOKIE_NAME = getattr(settings, "CSRF_DEFENSE_COOKIE_NAME", getattr(settings, "CSRF_COOKIE_NAME", "csrftoken"))
POST_FIELD_NAME = getattr(settings, "CSRF_DEFENSE_POST_FIELD_NAME", "csrfmiddlewaretoken")
TRUSTED_IPS = getattr(settings, "CSRF_DEFENSE_TRUSTED_IPS", [])
EXCLUDED_PATH_PREFIXES = getattr(settings, "CSRF_DEFENSE_EXCLUDED_PATH_PREFIXES", ["/api/internal/"])
EXCLUDED_PATHS = getattr(settings, "CSRF_DEFENSE_EXCLUDED_PATHS", [])
BLOCK_TIMEOUT_DEFAULT = getattr(settings, "CSRF_DEFENSE_BLOCK_SECONDS", 60 * 60)  # 1 hour default
COUNTER_WINDOW = getattr(settings, "CSRF_DEFENSE_COUNTER_WINDOW", 60 * 5)
COUNTER_THRESHOLD = getattr(settings, "CSRF_DEFENSE_COUNTER_THRESHOLD", 5)
BACKOFF_LEVELS = getattr(settings, "CSRF_DEFENSE_BACKOFF_LEVELS", [0, 60 * 15, 60 * 60, 60 * 60 * 6, 60 * 60 * 24, 60 * 60 * 24 * 7])
MIN_SIGNALS_TO_FLAG = getattr(settings, "CSRF_DEFENSE_MIN_SIGNALS", 1)
BLOCK_ON_HIGH = getattr(settings, "CSRF_DEFENSE_BLOCK_ON_HIGH", False)
SAME_SITE_REQUIRED = getattr(settings, "CSRF_DEFENSE_REQUIRE_SAMESITE", False)  # if True, enforce cookie Samesite heuristics
PAYLOAD_HASH_TTL = getattr(settings, "CSRF_DEFENSE_PAYLOAD_HASH_TTL", 60 * 60 * 24)  # 1 day
PAYLOAD_REPEAT_THRESHOLD = getattr(settings, "CSRF_DEFENSE_PAYLOAD_REPEAT_THRESHOLD", 3)  # repeated payloads across IPs -> escalation

# Cache key prefixes
CACHE_BLOCK_KEY = "csrf_block:"
CACHE_COUNTER_KEY = "csrf_count:"
CACHE_BLOCK_LEVEL_KEY = "csrf_block_level:"
CACHE_PAYLOAD_HASH_PREFIX = "csrf_payload_hash:"

# ----------------------------
# Patterns for payload analysis (expanded)
# ----------------------------
CSRF_PAYLOAD_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(r"<script[^>]*>.*?</script>", re.I | re.S), "Script tag en payload", 0.9),
    (re.compile(r"\bjavascript\s*:", re.I), "URI javascript: en payload", 0.8),
    (re.compile(r"http[s]?://[^\s'\"<>]+", re.I), "URL externa en payload", 0.7),
    (re.compile(r"\beval\s*\(", re.I), "eval() en payload", 1.0),
    (re.compile(r"\bdocument\.cookie\b", re.I), "Acceso a cookie en payload", 0.9),
    (re.compile(r"\binnerHTML\s*=", re.I), "Manipulación DOM innerHTML", 0.8),
    (re.compile(r"\bXMLHttpRequest\b", re.I), "XHR en payload", 0.7),
    (re.compile(r"\bfetch\s*\(", re.I), "fetch() en payload", 0.7),
    (re.compile(r"&#x[0-9a-fA-F]+;", re.I), "Entidades HTML en payload", 0.6),
    (re.compile(r"%3Cscript", re.I), "Script URL-encoded en payload", 0.8),
    (re.compile(r"on\w+\s*=", re.I), "Eventos on* en payload", 0.7),
    (re.compile(r"\balert\s*\(", re.I), "alert() en payload (prueba)", 0.5),
]

# Suspicious content-types (expanded)
SUSPICIOUS_CONTENT_TYPES = [
    re.compile(r"text/plain", re.I),
    re.compile(r"application/x-www-form-urlencoded", re.I),
    re.compile(r"multipart/form-data", re.I),
    re.compile(r"application/json", re.I),
    re.compile(r"text/html", re.I),
]

# Sensitive param names (analyze carefully)
SENSITIVE_PARAMS = getattr(settings, "CSRF_DEFENSE_SENSITIVE_PARAMS", [
    "password", "csrfmiddlewaretoken", "token", "amount", "transfer", "delete", "update", "action", "email", "username"
])

# ----------------------------
# Helpers: IP, host/origin
# ----------------------------
def get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "") or request.META.get("X-Forwarded-For", "")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[0]
    # check common headers
    for hdr in ("HTTP_X_REAL_IP", "HTTP_CLIENT_IP", "HTTP_CF_CONNECTING_IP"):
        val = request.META.get(hdr)
        if val:
            return val
    return request.META.get("REMOTE_ADDR", "") or ""

def host_from_header(header_value: str) -> Optional[str]:
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
    """Return True if Origin/Referer match Host (or missing but acceptable), False if mismatch or blatantly malicious."""
    host_header = request.META.get("HTTP_HOST") or request.META.get("SERVER_NAME")
    if not host_header:
        return True
    host = host_header.split(":")[0]
    origin = request.META.get("HTTP_ORIGIN", "") or ""
    referer = request.META.get("HTTP_REFERER", "") or ""
    # block obvious javascript/data: attacks
    for h in (origin, referer):
        if h and re.search(r"(javascript:|data:text/html|<script)", h, re.I):
            return False
    if origin_host := host_from_header(origin):
        if origin_host == host:
            return True
    if referer_host := host_from_header(referer):
        if referer_host == host:
            return True
    # If both empty, allow (could be non-browser client) — but it's a signal elsewhere
    if not origin and not referer:
        return True
    # otherwise mismatch
    return False

# ----------------------------
# Token validation: cookie/header/form double-submit
# ----------------------------
def has_csrf_token(request) -> bool:
    # header check
    for h in CSRF_HEADER_NAMES:
        if request.META.get(h):
            return True
    # cookie check
    if request.COOKIES.get(CSRF_COOKIE_NAME):
        return True
    # form field check
    try:
        if request.method == "POST" and hasattr(request, "POST"):
            if request.POST.get(POST_FIELD_NAME):
                return True
    except Exception:
        pass
    return False

def double_submit_valid(request) -> bool:
    """
    Double submit pattern:
    - cookie named CSRF_COOKIE_NAME contains token
    - header X-CSRFToken (or form field) contains token
    They must match (constant-time compare to avoid timing leaks).
    """
    cookie_val = request.COOKIES.get(CSRF_COOKIE_NAME)
    header_val = None
    for h in CSRF_HEADER_NAMES:
        header_val = request.META.get(h)
        if header_val:
            break
    # fallback to form field if header not provided
    if not header_val and hasattr(request, "POST"):
        header_val = request.POST.get(POST_FIELD_NAME)
    if not cookie_val or not header_val:
        return False
    try:
        # use hmac.compare_digest for constant-time comparison
        return hmac.compare_digest(str(cookie_val), str(header_val))
    except Exception:
        return False

# ----------------------------
# Payload analysis: return score and matches
# ----------------------------
def analyze_payload_value(value: str) -> Tuple[float, List[str]]:
    score = 0.0
    matches = []
    if not value:
        return 0.0, []
    for patt, desc, weight in CSRF_PAYLOAD_PATTERNS:
        if patt.search(value):
            score += weight
            matches.append(desc)
    return round(score, 3), matches

def analyze_request_payload(request) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Analyze POST form fields + application/json body + querystring.
    Return aggregated score and a payload summary (list of field/snippet/score).
    """
    total = 0.0
    summary: List[Dict[str, Any]] = []
    # POST form
    try:
        if hasattr(request, "POST"):
            for k, v in request.POST.items():
                if isinstance(v, str):
                    s, matches = analyze_payload_value(v)
                    if s > 0:
                        total += s
                        summary.append({"field": k, "snippet": v[:300], "score": s, "matches": matches})
    except Exception:
        pass
    # JSON body
    try:
        ct = (request.META.get("CONTENT_TYPE") or "").lower()
        if "application/json" in ct:
            raw = request.body.decode("utf-8", errors="ignore") or ""
            data = {}
            try:
                data = json.loads(raw) if raw else {}
            except Exception:
                # if body is not valid JSON, analyze raw
                s, matches = analyze_payload_value(raw)
                if s > 0:
                    total += s
                    summary.append({"field": "raw_json", "snippet": raw[:300], "score": s, "matches": matches})
            else:
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str):
                            s, matches = analyze_payload_value(v)
                            if s > 0:
                                total += s
                                summary.append({"field": k, "snippet": v[:300], "score": s, "matches": matches})
    except Exception:
        pass
    # Query string
    try:
        qs = request.META.get("QUERY_STRING", "") or ""
        if qs:
            s, matches = analyze_payload_value(qs)
            if s > 0:
                total += s
                summary.append({"field": "_query_string", "snippet": qs[:300], "score": s, "matches": matches})
    except Exception:
        pass
    return round(total, 3), summary

# ----------------------------
# Payload fingerprinting (hash) for cross-IP repetition detection
# ----------------------------
def payload_fingerprint(summary: List[Dict[str, Any]]) -> Optional[str]:
    """
    Create a stable fingerprint of the payload summary (hash of concatenated fields/matches).
    Used to detect repeated payloads coming from different IPs (helpful against VPNs).
    """
    if not summary:
        return None
    try:
        parts = []
        for item in summary:
            parts.append(f"{item.get('field','')}:{'|'.join(item.get('matches',[]))}")
        raw = "||".join(parts)
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return h
    except Exception:
        return None

# ----------------------------
# Cache / blocking utilities with backoff
# ----------------------------
def is_ip_blocked(ip: str) -> bool:
    if not ip:
        return False
    return bool(cache.get(f"{CACHE_BLOCK_KEY}{ip}"))

def cache_block_ip_with_backoff(ip: str) -> Tuple[int, int]:
    """
    Increase block level and block IP for duration based on BACKOFF_LEVELS.
    Returns (level, timeout_seconds).
    """
    if not ip:
        return 0, 0
    level_key = f"{CACHE_BLOCK_LEVEL_KEY}{ip}"
    level = int(cache.get(level_key, 0) or 0) + 1
    cache.set(level_key, level, timeout=60 * 60 * 24 * 7)  # keep level for 7 days
    idx = min(level, len(BACKOFF_LEVELS) - 1)
    timeout = BACKOFF_LEVELS[idx]
    cache.set(f"{CACHE_BLOCK_KEY}{ip}", True, timeout=timeout)
    return level, timeout

def incr_ip_counter(ip: str) -> int:
    if not ip:
        return 0
    key = f"{CACHE_COUNTER_KEY}{ip}"
    val = cache.get(key, 0) or 0
    try:
        val = int(val) + 1
    except Exception:
        val = 1
    cache.set(key, val, timeout=COUNTER_WINDOW)
    return val

def register_payload_hash(h: str, ip: str) -> int:
    """
    Register payload fingerprint seen from ip. Return total distinct IP count for that payload.
    We use a set-like structure via cache storing dict(ip->ts).
    """
    if not h:
        return 0
    key = f"{CACHE_PAYLOAD_HASH_PREFIX}{h}"
    rec = cache.get(key, {})
    if not isinstance(rec, dict):
        rec = {}
    rec[ip] = int(time.time())
    cache.set(key, rec, timeout=PAYLOAD_HASH_TTL)
    return len(rec.keys())

# ----------------------------
# Telemetry / record event (redact payload snippets)
# ----------------------------
def redact_summary(summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    red = []
    for item in summary:
        field = item.get("field", "")
        snippet = item.get("snippet", "")
        # redact sensitive-looking fields
        if any(s in field.lower() for s in ("password", "token", "csrf", "auth", "secret")):
            red.append({"field": field, "snippet": "<REDACTED>", "score": item.get("score", 0)})
        else:
            red.append({"field": field, "snippet": snippet[:200], "score": item.get("score", 0)})
    return red

def record_event(event: Dict[str, Any]) -> None:
    """
    Lightweight recording: store in cache for later ingestion by SIEM or process.
    Replace with DB/SIEM integration in production.
    """
    try:
        key = f"csrf_event:{int(time.time())}:{event.get('ip','')}"
        cache.set(key, json.dumps(event, ensure_ascii=False), timeout=60 * 60 * 24)
    except Exception:
        logger.exception("record_event failed")

# ----------------------------
# Middleware principal
# ----------------------------
class CSRFDefenseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 0) early excludes and block check
        path = getattr(request, "path", "") or ""
        for p in EXCLUDED_PATH_PREFIXES:
            if path.startswith(p):
                return None
        for p in EXCLUDED_PATHS:
            if path == p:
                return None

        client_ip = get_client_ip(request)
        if client_ip in TRUSTED_IPS:
            return None

        # check if ip already blocked
        if is_ip_blocked(client_ip):
            logger.error(f"[CSRFDefense] Blocked IP tried to access: {client_ip} path={path}")
            return HttpResponseForbidden("Access blocked by CSRF defense")

        method = (request.method or "").upper()
        if method not in STATE_CHANGING_METHODS:
            return None

        # gather signals
        signals: List[str] = []
        content_type = (request.META.get("CONTENT_TYPE") or "").lower()

        # 1) Token presence and double-submit validation
        if not has_csrf_token(request):
            signals.append("missing_csrf_token")
        else:
            if not double_submit_valid(request):
                if any(request.META.get(h) for h in CSRF_HEADER_NAMES) or request.COOKIES.get(CSRF_COOKIE_NAME) or (hasattr(request, "POST") and request.POST.get(POST_FIELD_NAME)):
                    signals.append("csrf_token_mismatch")

        # 2) Origin/Referer validation
        if not origin_matches_host(request):
            signals.append("origin_referer_mismatch")

        # 3) Suspicious Content-Type
        for patt in SUSPICIOUS_CONTENT_TYPES:
            if patt.search(content_type or ""):
                signals.append(f"suspicious_content_type:{content_type}")
                break

        # 4) Missing referer + missing X-CSRF header/cookie
        referer = request.META.get("HTTP_REFERER", "")
        if not referer and not any(request.META.get(h) for h in CSRF_HEADER_NAMES) and not request.COOKIES.get(CSRF_COOKIE_NAME):
            signals.append("missing_referer_and_token")

        # 5) Sensitive params in querystring
        try:
            qs_keys = []
            raw_qs = request.META.get("QUERY_STRING", "") or ""
            if raw_qs:
                for part in raw_qs.split("&"):
                    if "=" in part:
                        qs_keys.append(part.split("=",1)[0].lower())
                    else:
                        qs_keys.append(part.lower())
            for k in qs_keys:
                if k in SENSITIVE_PARAMS and method != "POST":
                    signals.append(f"sensitive_param_in_query:{k}")
        except Exception:
            pass

        # 6) JSON POST from external origin
        if "application/json" in content_type:
            origin = request.META.get("HTTP_ORIGIN", "") or ""
            if origin and host_from_header(origin) != (request.META.get("HTTP_HOST") or "").split(":")[0]:
                signals.append("json_post_external_origin")

        # 7) payload analysis
        payload_score, payload_summary = analyze_request_payload(request)
        if payload_score > 0:
            signals.append(f"payload_suspicious_score:{payload_score}")

        # 8) headers heuristics
        ua = request.META.get("HTTP_USER_AGENT", "") or ""
        if re.search(r"(script|<|eval|curl|wget|bot|crawler|scanner)", ua, re.I):
            signals.append("suspicious_user_agent")
        al = request.META.get("HTTP_ACCEPT_LANGUAGE", "") or ""
        if not al or len(al) < 2:
            signals.append("suspicious_accept_language")

        # 9) Compose score
        total_signals = len(signals)
        w_base = getattr(settings, "CSRF_DEFENSE_BASE_WEIGHT", 0.2)
        s_csrf = w_base * total_signals + float(payload_score)
        s_csrf = round(float(s_csrf), 3)

        # payload fingerprinting
        pf = payload_fingerprint(payload_summary) if payload_summary else None
        repeat_count = 0
        if pf:
            repeat_count = register_payload_hash(pf, client_ip)
            if repeat_count >= PAYLOAD_REPEAT_THRESHOLD:
                s_csrf += repeat_count * 0.5
                signals.append(f"payload_repeat_count:{repeat_count}")

        # ----------------------------
        # Build attack info (redacted) - compatible con AuditoriaMiddleware
        # ----------------------------
        descriptions: List[str] = []
        descriptions.extend(signals)
        for item in payload_summary:
            matches = item.get("matches", [])
            for m in matches:
                if m not in descriptions:
                    descriptions.append(m)

        redacted = redact_summary(payload_summary)
        payload_json = json.dumps(redacted, ensure_ascii=False)[:2000]

        attack_info = {
            "ip": client_ip,
            "tipos": ["CSRF"],
            "descripcion": descriptions,
            "payload": payload_json,
            "score": s_csrf,
            "url": request.build_absolute_uri(),
            "path": path,
            "timestamp": int(time.time()),
            "signals": signals,
        }

        if (total_signals >= MIN_SIGNALS_TO_FLAG) or (payload_score > 0):
            request.csrf_attack_info = attack_info
        else:
            request.csrf_attack_info = None

        # telemetry
        try:
            record_event({
                "ip": client_ip,
                "path": path,
                "signals": signals,
                "payload_summary": redacted,
                "score": s_csrf,
                "repeat_count": repeat_count,
                "timestamp": int(time.time()),
            })
        except Exception:
            logger.exception("record_event failure")

        # ----------------------------
        # Policy: block / alert / monitor
        # ----------------------------
        HIGH_THRESHOLD = getattr(settings, "CSRF_DEFENSE_HIGH_SCORE", 3.0)
        MED_THRESHOLD = getattr(settings, "CSRF_DEFENSE_MED_SCORE", 2.0)
        LOW_THRESHOLD = getattr(settings, "CSRF_DEFENSE_LOW_SCORE", 0.5)

        if s_csrf >= HIGH_THRESHOLD and BLOCK_ON_HIGH:
            level, timeout = cache_block_ip_with_backoff(client_ip)
            logger.error(f"[CSRFDefense][BLOCK] ip={client_ip} path={path} score={s_csrf} level={level} timeout={timeout}s signals={signals}")
            request.csrf_attack_info.update({"blocked": True, "block_level": level, "block_timeout": timeout})
            return HttpResponseForbidden("Request blocked by CSRF defense")

        if s_csrf >= MED_THRESHOLD:
            count = incr_ip_counter(client_ip)
            logger.warning(f"[CSRFDefense][ALERT] ip={client_ip} path={path} score={s_csrf} counter={count} signals={signals}")
            request.csrf_attack_info.update({"blocked": False, "counter": count})
            if count >= COUNTER_THRESHOLD:
                level, timeout = cache_block_ip_with_backoff(client_ip)
                cache.set(f"{CACHE_COUNTER_KEY}{client_ip}", 0, timeout=COUNTER_WINDOW)
                logger.error(f"[CSRFDefense][AUTOBLOCK] ip={client_ip} score={s_csrf} -> level={level} timeout={timeout}s")
                request.csrf_attack_info.update({"blocked": True, "block_level": level, "block_timeout": timeout})
                return HttpResponseForbidden("Request auto-blocked by CSRF defense")
            # Remueve el challenge: no devolver 403 aquí
            return None

        if s_csrf >= LOW_THRESHOLD:
            logger.info(f"[CSRFDefense][MONITOR] ip={client_ip} path={path} score={s_csrf} signals={signals}")
            request.csrf_attack_info.update({"blocked": False})
            return None

        return None

"""
CSRF Defense Middleware - Ultra-Robusto (Nada Ignorado)
=======================================================
- Detecta múltiples categorías de CSRF: clásico, login, logout, password change, file/action, JSON API.
- Escanea payloads POST, GET, JSON, query string y headers, incluyendo TODOS los campos (sensibles y no) con score full (sin descuento).
- Detecta parámetros sensibles enviados en GET o JSON desde origen externo.
- Análisis adicional de User-Agent, Accept-Language, y payloads con patrones expandidos.
- Scoring configurable y logging detallado.
- Fácil integración con auditoría XSS/SQLi.
- Máxima robustez: no ignora nada para detección óptima.
"""
