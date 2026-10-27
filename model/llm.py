"""Ollama-backed LLM layer for the "Ask AI" chatbot.

The LLM only ever *explains* laptops that RAG retrieval (model/rag.py) found in
our own dataset - it can never invent one. All prompting happens server-side so
no model/key details leak into the frontend, and the whole stack stays local
and free (Ollama + mistral on the user's machine).

Host resolution (this project runs inside WSL while Ollama runs on Windows):
  1. OLLAMA_BASE_URL env var (explicit override)
  2. http://localhost:11434            (mirrored WSL networking / native Linux)
  3. WSL NAT gateway IP                (default route -> Windows host)
  4. resolv.conf nameserver IP         (alternate Windows host address)

Candidates are probed against GET /api/version with a short timeout; the first
one that answers is cached until a connection failure resets it. This keeps the
API working across reboots even though the NAT gateway IP changes.
"""

import ipaddress
import json
import os

DEFAULT_MODEL = "mistral"
DEFAULT_PORT = 11434
PROBE_TIMEOUT_S = 1.0
CHAT_TIMEOUT_S = 240.0
MAX_HISTORY_TURNS = 6

_cache = {"base_url": None}


class LLMUnavailable(Exception):
    """Raised when no Ollama server could be reached or a request fails."""


# ---------------------------------------------------------------------------
# Host resolution
# ---------------------------------------------------------------------------

def _gateway_ips():
    """Default-route gateways from /proc/net/route (Windows host under WSL NAT)."""
    ips = []
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) > 2 and parts[1] == "00000000":
                    raw = bytes.fromhex(parts[2])
                    ips.append(ipaddress.ip_address(raw[::-1]).compressed)
    except OSError:
        pass
    return ips


def _nameserver_ips():
    ips = []
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.startswith("nameserver"):
                    ip = line.split()[1]
                    try:
                        ipaddress.ip_address(ip)
                        ips.append(ip)
                    except ValueError:
                        pass
    except OSError:
        pass
    return ips


def candidate_urls():
    """Ordered list of Ollama base URLs to probe."""
    urls = []
    env_url = os.environ.get("OLLAMA_BASE_URL", "").strip().rstrip("/")
    if env_url:
        urls.append(env_url)
    for host in ["localhost", "127.0.0.1", *_gateway_ips(), *_nameserver_ips()]:
        url = f"http://{host}:{DEFAULT_PORT}"
        if url not in urls:
            urls.append(url)
    return urls


def reset_host_cache():
    _cache["base_url"] = None


def resolve_base_url(force=False):
    """Find a reachable Ollama server and cache its base URL.

    Returns the URL string, or raises LLMUnavailable with every candidate tried.
    """
    import httpx

    if not force and _cache["base_url"]:
        return _cache["base_url"]

    tried = []
    for url in candidate_urls():
        try:
            r = httpx.get(f"{url}/api/version", timeout=PROBE_TIMEOUT_S)
            if r.status_code == 200:
                _cache["base_url"] = url
                return url
        except httpx.HTTPError:
            pass
        tried.append(url)
    raise LLMUnavailable(
        "No Ollama server reachable. Tried: "
        + ", ".join(tried or ["(none)"])
        + ". Start Ollama ('ollama serve' or the desktop app) or set OLLAMA_BASE_URL."
    )


def model_name():
    return os.environ.get("OLLAMA_MODEL", "").strip() or DEFAULT_MODEL


def is_available():
    """True when an Ollama server answers the version probe."""
    try:
        resolve_base_url()
        return True
    except LLMUnavailable:
        return False


# ---------------------------------------------------------------------------
# Chat generation
# ---------------------------------------------------------------------------

def chat(messages, options=None, stream=False):
    """Call Ollama /api/chat. Returns the full reply text (or a response object
    iterator when stream=True). Raises LLMUnavailable on connection problems."""
    import httpx

    base = resolve_base_url()
    payload = {
        "model": model_name(),
        "messages": messages,
        "stream": stream,
        "options": options or {},
    }
    try:
        if stream:
            return _stream_chunks(base, payload)
        resp = httpx.post(f"{base}/api/chat", json=payload, timeout=CHAT_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()
    except httpx.HTTPError as exc:
        reset_host_cache()
        raise LLMUnavailable(f"Ollama request failed: {exc}") from exc


def stream_chat(messages, options=None):
    """Generator yielding reply text chunks as they arrive from Ollama."""
    gen = chat(messages, options=options, stream=True)
    yield from gen


def _stream_chunks(base, payload):
    import httpx

    try:
        with httpx.stream("POST", f"{base}/api/chat", json=payload, timeout=CHAT_TIMEOUT_S) as resp:
            if resp.status_code != 200:
                raise LLMUnavailable(f"Ollama returned HTTP {resp.status_code}")
            for line in resp.iter_lines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                delta = obj.get("message", {}).get("content", "")
                if delta:
                    yield delta
                if obj.get("done"):
                    break
    except httpx.HTTPError as exc:
        reset_host_cache()
        raise LLMUnavailable(f"Ollama stream failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Grounded prompt construction (retrieval results -> messages)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are the Ask AI assistant for LaptopFinder Nepal, a laptop shopping "
    "website for customers in Nepal.\n"
    "Answer ONLY using the laptop data provided in the conversation - it comes "
    "straight from our store dataset.\n"
    "Rules:\n"
    "- Cite exact brand names, model names and NPR prices as given in the data.\n"
    "- Never invent laptops, specs, prices, stock or warranty information.\n"
    "- The laptop specs and current price are already visible on the user's "
    "screen, so do NOT repeat or re-describe the laptop's specs or price - go "
    "straight to answering the question in the first sentence.\n"
    "- Short follow-ups like 'and this one?', 'what about its battery?' or "
    "'is the cheaper one better?' refer to the laptops already discussed in "
    "this conversation, especially the laptop the user is currently viewing. "
    "Use that context - do not treat a short follow-up as a brand-new search.\n"
    "- If the provided data does not answer the question, say plainly that you "
    "don't have that information and suggest what to search instead.\n"
    "- Be concise, friendly and helpful; keep answers under 120 words unless "
    "comparing several laptops.\n"
    "- All prices are in Nepali Rupees (NPR)."
)


def format_focus_laptop(laptop):
    """One-line spec summary of the laptop the user is currently viewing."""
    gpu = " ".join(x for x in (laptop.get("gpu_brand"), laptop.get("gpu_model")) if x) or "integrated graphics"

    def num(key):
        try:
            return float(laptop.get(key) or 0)
        except (TypeError, ValueError):
            return 0.0

    ram = num("ram_gb")
    storage_gb = num("storage_gb")
    price = num("price_npr")
    screen = num("screen_size")
    storage = f"{storage_gb:.0f}GB {laptop.get('storage_type')}" if storage_gb else "storage not listed"
    screen_txt = f"{screen:.0f} inch" if screen else None
    bits = [
        str(laptop.get("brand", "")),
        str(laptop.get("cpu_brand", "")) + " " + str(laptop.get("cpu_model", "")),
        gpu,
        f"{ram:.0f}GB RAM",
        storage,
    ]
    if screen_txt:
        bits.append(screen_txt)
    if price:
        bits.append(f"NPR {price:,.0f}")
    purpose = laptop.get("purpose")
    if purpose:
        bits.append(f"suited for {purpose}")
    return ", ".join(b.strip() for b in bits if b and b.strip())


def build_context_block(sources, focus_laptop=None):
    """Numbered spec-sheet block fed to the model as grounding context."""
    lines = []
    if focus_laptop:
        lines.append(f"The user is currently viewing this laptop:\n{format_focus_laptop(focus_laptop)}")
    if sources:
        lines.append("Other relevant laptops from our dataset (most relevant first):")
        for src in sources:
            lines.append(f"[{src['rank']}] {src['document']}")
    return "\n\n".join(lines)


def clean_history(history):
    """Keep only the last few valid user/assistant turns."""
    cleaned = []
    for msg in history or []:
        role = msg.get("role")
        content = str(msg.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content})
    return cleaned[-MAX_HISTORY_TURNS:]


def build_chat_messages(question, sources, history=None, focus_laptop=None):
    """Assemble the grounded message list for Ollama."""
    context = build_context_block(sources, focus_laptop=focus_laptop)
    grounded_question = (
        f"{context}\n\nQuestion: {question}"
        if context
        else question
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *clean_history(history),
        {"role": "user", "content": grounded_question},
    ]


def default_options():
    """Sampling limits that keep replies focused and inference time bounded."""
    return {
        "num_predict": 320,
        "temperature": 0.4,
        "num_ctx": 2048,
    }
