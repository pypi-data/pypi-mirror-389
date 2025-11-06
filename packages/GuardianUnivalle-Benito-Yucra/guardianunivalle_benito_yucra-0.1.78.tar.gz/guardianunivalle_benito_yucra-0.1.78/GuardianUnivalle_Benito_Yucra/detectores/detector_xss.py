# xss_defense.py
# GuardianUnivalle_Benito_Yucra/detectores/xss_defense.py
# xss_defense_complete.py
from __future__ import annotations
import json
import logging
import re
import math
from typing import List, Tuple, Dict, Any
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

try:
    import bleach
    _BLEACH_AVAILABLE = True
except Exception:
    _BLEACH_AVAILABLE = False

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger("xssdefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

# ----------------------------
# Patrones XSS robustos (incluye Polyglot / CSS / SVG / JSON / JS)
# ----------------------------
XSS_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
    # Scripts directos y ofuscados
    (re.compile(r"<\s*script\b", re.I), "<script> directo", 0.95),
    (re.compile(r"<\s*s\s*c\s*r\s*i\s*p\s*t\b", re.I), "<script> ofuscado", 0.90),
    (re.compile(r"\b(eval|Function|setTimeout|setInterval|document\.write)\s*\(", re.I),
     "Ejecución JS dinámica", 0.88),
    (re.compile(r"\bjavascript\s*:", re.I), "URI javascript:", 0.85),
    (re.compile(r"\bdata\s*:\s*text\/html\b", re.I), "URI data:text/html", 0.82),
    (re.compile(r"\bvbscript\s*:", re.I), "URI vbscript:", 0.7),
    # Iframes, objetos, embeds, SVG, MathML
    (re.compile(r"<\s*(iframe|embed|object|svg|math|meta)\b", re.I), "Iframe/Embed/Object/SVG/Meta", 0.88),
    (re.compile(r"<\s*img\b[^>]*\bonerror\b", re.I), "<img onerror>", 0.86),
    (re.compile(r"<\s*svg\b[^>]*\bonload\b", re.I), "SVG onload/on*", 0.84),
    # Atributos de evento on*
    (re.compile(r"\s+on[a-zA-Z]+\s*=", re.I), "Atributo evento on*", 0.80),
    (re.compile(r"<\s*(a|img|body|div|span|form|input|button)\b[^>]*on[a-zA-Z]+\s*=", re.I),
     "Elemento con evento on*", 0.82),
    # InnerHTML / DOM
    (re.compile(r"\binnerHTML\s*=\s*.*[<>\"']", re.I), "Asignación innerHTML", 0.85),
    (re.compile(r"\bdocument\.getElementById\s*\(\s*.*\)\.innerHTML", re.I), "Manipulación DOM innerHTML", 0.80),
    # JSON / eval inseguro
    (re.compile(r"\bJSON\.parse\(|\beval\(\s*JSON", re.I), "JSON parse/eval inseguro", 0.75),
    # CSS
    (re.compile(r"\bstyle\s*=\s*[\"'][^\"']*(expression\s*\(|url\s*\(\s*javascript:)", re.I), "CSS expression/url()", 0.66),
    (re.compile(r"@import\s+url\s*\(", re.I), "CSS @import vector", 0.45),
    # Comentarios / CDATA / escapes
    (re.compile(r"<!\[CDATA\[|\/\/\s*<\s*!\s*\[CDATA\[", re.I), "CDATA/comentarios para evasión", 0.48),
    (re.compile(r"&#x[0-9a-fA-F]+;|&#\d+;", re.I), "Entidades HTML/encoding", 0.70),
    (re.compile(r"%3C\s*script|%3Cscript%3E", re.I), "Tags URL-encoded", 0.68),
]

# ----------------------------
# Campos sensibles y descuento
# ----------------------------
SENSITIVE_FIELDS = ["password", "csrfmiddlewaretoken", "token", "auth"]
SENSITIVE_DISCOUNT = 0.5

# ----------------------------
# Función de saturación tipo sigmoide
# ----------------------------
SATURATION_C = getattr(settings, "XSS_DEFENSE_SATURATION_C", 1.5)
SATURATION_ALPHA = getattr(settings, "XSS_DEFENSE_SATURATION_ALPHA", 2.0)

def saturate_score(raw_score: float) -> float:
    try:
        x = float(raw_score)
        alpha = float(SATURATION_ALPHA)
        c = float(SATURATION_C)
        return 1.0 / (1.0 + math.exp(-alpha * (x - c)))
    except Exception:
        return 0.0

# ----------------------------
# IP robusta
# ----------------------------
def _is_valid_ip(ip: str) -> bool:
    try:
        import ipaddress
        ipaddress.ip_address(ip)
        return True
    except Exception:
        return False

def get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[0]
    for h in ("HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP", "HTTP_CLIENT_IP"):
        v = request.META.get(h)
        if v and _is_valid_ip(v):
            return v
    return request.META.get("REMOTE_ADDR") or ""

# ----------------------------
# Extraer payload (JSON, POST, raw)
# ----------------------------
def extract_body_as_map(request) -> Dict[str, Any]:
    try:
        ct = request.META.get("CONTENT_TYPE", "")
        if "application/json" in ct:
            raw = request.body.decode("utf-8") or "{}"
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
                return {"raw": raw}
            except Exception:
                return {"raw": raw}
        try:
            post = request.POST.dict()
            if post:
                return post
        except Exception:
            pass
        raw = request.body.decode("utf-8", errors="ignore")
        if raw:
            return {"raw": raw}
    except Exception:
        pass
    return {}

# ----------------------------
# Detect XSS en valor (diminishing returns)
# ----------------------------
def detect_xss_in_value(value: str, is_sensitive: bool = False) -> Tuple[float, List[str], List[str]]:
    if not value:
        return 0.0, [], []
    score_total = 0.0
    descripcion = []
    matches = []
    value = value.lower().strip()
    if _BLEACH_AVAILABLE:
        cleaned = bleach.clean(value, strip=True)
        if cleaned != value:
            score_total += 0.5
            descripcion.append("Contenido alterado por sanitización (bleach)")
    for patt, msg, weight in XSS_PATTERNS:
        occ = len(patt.findall(value))
        if occ > 0:
            added = sum(weight * (0.5 ** i) for i in range(occ))  # diminishing returns
            if is_sensitive:
                added *= SENSITIVE_DISCOUNT
            score_total += added
            descripcion.append(msg)
            matches.append(patt.pattern)
    return round(score_total, 3), descripcion, matches

# ----------------------------
# Conversión a probabilidad
# ----------------------------
def weight_to_prob(w: float) -> float:
    try:
        q = 1.0 - math.exp(-max(w, 0.0))
        return min(max(q, 0.0), 0.999999)
    except Exception:
        return min(max(w, 0.0), 0.999999)

def combine_probs(qs: List[float]) -> float:
    prod = 1.0
    for q in qs:
        prod *= (1.0 - q)
    return 1.0 - prod

# ----------------------------
# Middleware XSS robusto
# ----------------------------
class XSSDefenseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        client_ip = get_client_ip(request)
        trusted_ips: List[str] = getattr(settings, "XSS_DEFENSE_TRUSTED_IPS", [])
        if client_ip in trusted_ips:
            return None
        excluded_paths: List[str] = getattr(settings, "XSS_DEFENSE_EXCLUDED_PATHS", [])
        if any(request.path.startswith(p) for p in excluded_paths):
            return None

        data = extract_body_as_map(request)
        qs = request.META.get("QUERY_STRING", "")
        if qs:
            data["_query_string"] = qs
        if not data:
            return None

        total_score = 0.0
        all_descriptions: List[str] = []
        global_prob_list: List[float] = []
        payload_summary = []

        if isinstance(data, dict):
            for key, value in data.items():
                is_sensitive = key.lower() in SENSITIVE_FIELDS
                vtext = value
                if isinstance(value, (dict, list)):
                    try:
                        vtext = json.dumps(value, ensure_ascii=False)
                    except Exception:
                        vtext = str(value)
                else:
                    vtext = str(value or "")
                s, descs, matches = detect_xss_in_value(vtext, is_sensitive)
                total_score += s
                all_descriptions.extend(descs)
                for m in matches:
                    q = weight_to_prob(s)
                    global_prob_list.append(q)
                if s > 0:
                    payload_summary.append({"field": key, "snippet": vtext[:300], "sensitive": is_sensitive})
        else:
            raw = str(data)
            s, descs, matches = detect_xss_in_value(raw)
            total_score += s
            all_descriptions.extend(descs)
            for m in matches:
                q = weight_to_prob(s)
                global_prob_list.append(q)
            if s > 0:
                payload_summary.append({"field": "raw", "snippet": raw[:500], "sensitive": False})

        if total_score == 0:
            return None

        p_attack = combine_probs(global_prob_list) if global_prob_list else 0.0
        s_norm = saturate_score(total_score)
        url = request.build_absolute_uri()
        payload_for_request = json.dumps(payload_summary, ensure_ascii=False)[:2000]

        logger.warning(
            "[XSSDetect] IP=%s URL=%s ScoreRaw=%.3f ScoreNorm=%.3f Prob=%.3f Desc=%s",
            client_ip, url, total_score, s_norm, p_attack, all_descriptions
        )

        request.xss_attack_info = {
            "ip": client_ip,
            "tipos": ["XSS"],
            "descripcion": all_descriptions,
            "payload": payload_for_request,
            "score_raw": total_score,
            "score_norm": s_norm,
            "prob": p_attack,
            "url": url,
        }
        return None

# =====================================================
# ===              INFORMACIÓN EXTRA                ===
# =====================================================
"""
Algoritmos relacionados:
    - Se recomienda almacenar los payloads XSS cifrados con AES-GCM
      para confidencialidad e integridad.

Contribución a fórmula de amenaza S:
    S_xss = w_xss * detecciones_xss
    Ejemplo: S_xss = 0.3 * 2 = 0.6
"""
