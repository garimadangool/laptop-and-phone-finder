import sys
import os
import csv
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from fastapi.testclient import TestClient
from api.main import app
from model import rag
from model import llm
from model.recommend import load_data


client = TestClient(app)

N_INDEX_ROWS = 150


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _slice_csv(dest_path, step=35):
    rows = load_data()
    sampled = rows[::step][:N_INDEX_ROWS]
    if len(sampled) < 10:
        sampled = rows[:N_INDEX_ROWS]
    with open(dest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sampled)
    return dest_path, len(sampled)


@pytest.fixture(scope="module")
def rag_env(tmp_path_factory):
    """Small persisted RAG index shared by this module's endpoint tests."""
    work = tmp_path_factory.mktemp("llm")
    csv_path, n_rows = _slice_csv(str(work / "slice.csv"))
    index_dir = str(work / "chroma")
    meta = rag.build_index(data_path=csv_path, persist_dir=index_dir)
    rag.set_index_dir(index_dir)
    llm.reset_host_cache()
    yield {"index_dir": index_dir, "csv_path": csv_path, "n_rows": n_rows}
    rag.reset_index_dir()
    llm.reset_host_cache()


@pytest.fixture(autouse=True)
def _no_real_ollama(monkeypatch):
    """Never let a test touch the network: kill host cache before/after."""
    llm.reset_host_cache()
    yield
    llm.reset_host_cache()


class FakeResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"HTTP {self.status_code}")


# ---------------------------------------------------------------------------
# Prompt construction (model/llm.py)
# ---------------------------------------------------------------------------

class TestBuildChatMessages:
    def test_system_prompt_present_with_grounding_rules(self):
        msgs = llm.build_chat_messages("best laptop?", [])
        assert msgs[0]["role"] == "system"
        body = msgs[0]["content"]
        assert "LaptopFinder Nepal" in body
        assert "ONLY" in body
        assert "NPR" in body
        assert "do NOT repeat or re-describe" in body
        assert "Short follow-ups" in body

    def test_question_and_context_documents_included(self):
        sources = [
            {"rank": 1, "document": "ASUS Core i7 laptop priced at NPR 90,000."},
            {"rank": 2, "document": "HP Ryzen 5 laptop priced at NPR 55,000."},
        ]
        msgs = llm.build_chat_messages("gaming under 100k?", sources)
        user_msg = msgs[-1]
        assert user_msg["role"] == "user"
        assert "[1] ASUS Core i7 laptop priced at NPR 90,000." in user_msg["content"]
        assert "[2] HP Ryzen 5 laptop priced at NPR 55,000." in user_msg["content"]
        assert "Question: gaming under 100k?" in user_msg["content"]

    def test_history_turns_kept_in_order(self):
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "and battery?"},
        ]
        msgs = llm.build_chat_messages("and weight?", [], history=history)
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user", "assistant", "user", "user"]
        assert msgs[1]["content"] == "hi"
        assert msgs[-1]["content"] == "and weight?"

    def test_history_truncated_and_invalid_roles_dropped(self):
        history = [{"role": "tool", "content": "x"}] + [
            {"role": "user", "content": f"q{i}"} for i in range(10)
        ]
        cleaned = llm.clean_history(history)
        assert len(cleaned) <= llm.MAX_HISTORY_TURNS
        assert all(m["role"] in ("user", "assistant") for m in cleaned)
        assert cleaned[-1]["content"] == "q9"

    def test_empty_content_entries_dropped(self):
        cleaned = llm.clean_history([{"role": "user", "content": "  "}, {"role": "user", "content": "ok"}])
        assert len(cleaned) == 1
        assert cleaned[0]["content"] == "ok"


class TestFocusLaptopFormatting:
    def test_full_record_rendered_with_price(self):
        line = llm.format_focus_laptop({
            "brand": "ASUS", "cpu_brand": "Intel", "cpu_model": "Core i7-11370H",
            "gpu_brand": "NVIDIA", "gpu_model": "RTX 3070", "ram_gb": 16,
            "storage_gb": 512, "storage_type": "SSD", "screen_size": 15.6,
            "price_npr": 129990, "purpose": "Gaming",
        })
        assert "ASUS" in line and "Core i7-11370H" in line and "RTX 3070" in line
        assert "NPR 129,990" in line
        assert "suited for Gaming" in line

    def test_partial_record_does_not_crash(self):
        line = llm.format_focus_laptop({"brand": "Dell"})
        assert "Dell" in line
        assert "storage not listed" in line

    def test_non_numeric_garbage_tolerated(self):
        line = llm.format_focus_laptop({"brand": "X", "ram_gb": "abc", "price_npr": None})
        assert "0GB RAM" in line
        assert "NPR" not in line


# ---------------------------------------------------------------------------
# Host resolution + availability
# ---------------------------------------------------------------------------

class TestHostResolution:
    def test_env_override_is_first_candidate(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.50:11434")
        urls = llm.candidate_urls()
        assert urls[0] == "http://192.168.1.50:11434"

    def test_default_candidates_include_localhost(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        urls = llm.candidate_urls()
        assert "http://localhost:11434" in urls
        assert urls == list(dict.fromkeys(urls))  # no duplicates

    def test_resolve_probes_and_caches(self, monkeypatch):
        calls = []

        def fake_get(url, timeout=None):
            calls.append(url)
            return FakeResp(status_code=500)

        # Only the second candidate answers successfully
        def fake_get_ok(url, timeout=None):
            calls.append(url)
            if "127.0.0.1" in url:
                return FakeResp(status_code=200, json_data={"version": "0"})
            return FakeResp(status_code=500)

        monkeypatch.setattr(httpx, "get", fake_get_ok)
        base = llm.resolve_base_url(force=True)
        assert "127.0.0.1" in base
        n_first = len(calls)
        base2 = llm.resolve_base_url()  # cached - no extra probing
        assert base2 == base and len(calls) == n_first

    def test_resolve_raises_when_nothing_answers(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.setattr(httpx, "get", lambda url, timeout=None: FakeResp(status_code=500))
        with pytest.raises(llm.LLMUnavailable):
            llm.resolve_base_url(force=True)

    def test_connection_errors_are_survived(self, monkeypatch):
        def boom(url, timeout=None):
            raise httpx.ConnectError("refused")

        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.setattr(httpx, "get", boom)
        with pytest.raises(llm.LLMUnavailable):
            llm.resolve_base_url(force=True)

    def test_is_available_true_and_false(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.setattr(httpx, "get", lambda url, timeout=None: FakeResp(status_code=200))
        assert llm.is_available() is True
        llm.reset_host_cache()
        monkeypatch.setattr(httpx, "get", lambda url, timeout=None: FakeResp(status_code=500))
        assert llm.is_available() is False

    def test_model_name_default_and_env(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        assert llm.model_name() == "mistral"
        monkeypatch.setenv("OLLAMA_MODEL", "llama2")
        assert llm.model_name() == "llama2"


# ---------------------------------------------------------------------------
# Chat generation against a mocked Ollama server
# ---------------------------------------------------------------------------

class TestChatGeneration:
    def test_chat_returns_reply_text(self, monkeypatch):
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured["url"] = url
            captured["payload"] = json
            return FakeResp(json_data={"message": {"content": "  Grounded answer!  \n"}})

        monkeypatch.setenv("OLLAMA_MODEL", "mistral")
        monkeypatch.setattr(httpx, "post", fake_post)
        llm._cache["base_url"] = "http://fake-host:11434"
        out = llm.chat([{"role": "user", "content": "q"}], options={"num_predict": 10})
        assert out == "Grounded answer!"
        assert captured["url"] == "http://fake-host:11434/api/chat"
        assert captured["payload"]["model"] == "mistral"
        assert captured["payload"]["stream"] is False
        assert captured["payload"]["options"] == {"num_predict": 10}

    def test_chat_http_error_raises_llm_unavailable_and_resets_cache(self, monkeypatch):
        def fail_post(url, json=None, timeout=None):
            raise httpx.HTTPError("server gone")

        monkeypatch.setattr(httpx, "post", fail_post)
        llm._cache["base_url"] = "http://fake-host:11434"
        with pytest.raises(llm.LLMUnavailable):
            llm.chat([{"role": "user", "content": "q"}])
        assert llm._cache["base_url"] is None  # cache reset -> will re-probe next time

    def test_stream_chunks_parse_ndjson_until_done(self, monkeypatch):
        lines = [
            json.dumps({"message": {"content": "Hi"}}),
            "",
            json.dumps({"message": {"content": " there"}, "done": True}),
            json.dumps({"message": {"content": "IGNORED"}}),
        ]

        class FakeStream:
            status_code = 200

            def iter_lines(self):
                return iter(lines)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(
            httpx, "stream",
            lambda method, url, json=None, timeout=None: FakeStream(),
        )
        chunks = list(llm._stream_chunks("http://fake-host:11434", {}))
        assert chunks == ["Hi", " there"]

    def test_stream_non_200_raises_unavailable(self, monkeypatch):
        class FakeStream:
            status_code = 503

            def iter_lines(self):
                return iter([])

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(
            httpx, "stream",
            lambda method, url, json=None, timeout=None: FakeStream(),
        )
        with pytest.raises(llm.LLMUnavailable):
            list(llm._stream_chunks("http://fake-host:11434", {}))

    def test_stream_chat_yields_via_chat(self, monkeypatch):
        monkeypatch.setattr(
            llm, "_stream_chunks",
            lambda base, payload: iter(["a", "b"]),
        )
        llm._cache["base_url"] = "http://fake-host:11434"
        assert list(llm.stream_chat([{"role": "user", "content": "q"}])) == ["a", "b"]


# ---------------------------------------------------------------------------
# API endpoints (LLM mocked, real RAG index)
# ---------------------------------------------------------------------------

QUESTION = {"question": "good gaming laptop under 80k", "top_n": 3}


class TestAskAiEndpoint:
    def test_happy_path_shape(self, rag_env, monkeypatch):
        monkeypatch.setattr(llm, "chat", lambda *a, **kw: "The ASUS TUF is your best bet.")
        res = client.post("/ask-ai", json=QUESTION)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "ASUS TUF" in data["answer"]
        assert data["model"] == "mistral"
        assert data["retrieved"] == len(data["sources"]) > 0
        assert isinstance(data["elapsed_ms"], int)
        src = data["sources"][0]
        assert set(src.keys()) == {"rank", "similarity", "laptop", "document"}
        assert src["rank"] == 1
        assert "npr" in src["document"].lower()

    def test_sources_are_grounded_in_dataset(self, rag_env, monkeypatch):
        monkeypatch.setattr(llm, "chat", lambda *a, **kw: "ok")
        res = client.post("/ask-ai", json=QUESTION)
        assert res.status_code == 200
        with open(rag_env["csv_path"]) as f:
            rows = [{k.lower(): v for k, v in row.items()} for row in csv.DictReader(f)]
        known = {(r["brand"], float(r["price_npr"])) for r in rows}
        for src in res.json()["sources"]:
            lt = src["laptop"]
            assert (lt["brand"], float(lt["price_npr"])) in known

    def test_prompt_receives_retrieved_context(self, rag_env, monkeypatch):
        seen = {}
        def fake_chat(messages, options=None, stream=False):
            seen["messages"] = messages
            return "answer"
        monkeypatch.setattr(llm, "chat", fake_chat)
        client.post("/ask-ai", json=QUESTION)
        user_msg = seen["messages"][-1]["content"]
        assert "Question: good gaming laptop under 80k" in user_msg
        assert "[1]" in user_msg  # numbered retrieved documents

    def test_focus_laptop_passed_into_prompt(self, rag_env, monkeypatch):
        seen = {}
        def fake_chat(messages, options=None, stream=False):
            seen["messages"] = messages
            return "answer"
        monkeypatch.setattr(llm, "chat", fake_chat)
        client.post("/ask-ai", json={
            **QUESTION,
            "question": "is this worth it?",
            "laptop": {
                "brand": "Dell", "cpu_brand": "Intel", "cpu_model": "Core i5",
                "gpu_brand": "NVIDIA", "gpu_model": "RTX 3050", "ram_gb": 8,
                "storage_gb": 512, "storage_type": "SSD", "screen_size": 15.6,
                "touchscreen": False, "os": "Windows", "weight_kg": 2.1,
                "price_npr": 75000, "purpose": "Gaming",
            },
        })
        assert "currently viewing" in seen["messages"][-1]["content"]
        assert "NPR 75,000" in seen["messages"][-1]["content"]

    def test_llm_down_maps_to_503(self, rag_env, monkeypatch):
        def unavailable(*a, **kw):
            raise llm.LLMUnavailable("No Ollama server reachable.")
        monkeypatch.setattr(llm, "chat", unavailable)
        res = client.post("/ask-ai", json=QUESTION)
        assert res.status_code == 503
        assert "Ollama" in res.json()["detail"]

    def test_no_retrieval_results_maps_to_503(self, rag_env, monkeypatch):
        res = client.post("/ask-ai", json={"question": "anything", "brand": "NoSuchBrand"})
        assert res.status_code == 503
        assert "No laptops matched" in res.json()["detail"]

    def test_missing_index_maps_to_503_with_hint(self, rag_env, monkeypatch, tmp_path):
        empty = str(tmp_path / "empty-chroma")
        os.makedirs(empty)
        rag.set_index_dir(empty)
        try:
            res = client.post("/ask-ai", json=QUESTION)
        finally:
            rag.set_index_dir(rag_env["index_dir"])
        assert res.status_code == 503
        assert "python3 -m model.rag" in res.json()["detail"]

    def test_blank_question_rejected(self, rag_env, monkeypatch):
        res = client.post("/ask-ai", json={"question": "   "})
        assert res.status_code == 422

    def test_invalid_history_role_rejected(self, rag_env, monkeypatch):
        monkeypatch.setattr(llm, "chat", lambda *a, **kw: "ok")
        res = client.post("/ask-ai", json={
            **QUESTION,
            "history": [{"role": "tool", "content": "nope"}],
        })
        assert res.status_code == 422

    def test_valid_history_round_trips_to_prompt(self, rag_env, monkeypatch):
        seen = {}
        def fake_chat(messages, options=None, stream=False):
            seen["messages"] = messages
            return "ok"
        monkeypatch.setattr(llm, "chat", fake_chat)
        res = client.post("/ask-ai", json={
            **QUESTION,
            "question": "cheaper?",
            "history": [
                {"role": "user", "content": "first question"},
                {"role": "assistant", "content": "first answer"},
            ],
        })
        assert res.status_code == 200
        assert seen["messages"][1] == {"role": "user", "content": "first question"}
        assert seen["messages"][2] == {"role": "assistant", "content": "first answer"}


class TestAskAiStreamEndpoint:
    def test_stream_events_start_delta_done(self, rag_env, monkeypatch):
        monkeypatch.setattr(llm, "stream_chat", lambda messages, options=None: iter(["Go ", "ASUS!"]))
        res = client.post("/ask-ai/stream", json=QUESTION)
        assert res.status_code == 200
        events = [json.loads(line) for line in res.text.strip().splitlines()]
        types = [e["type"] for e in events]
        assert types[0] == "start"
        assert set(types[1:-1]) == {"delta"}
        assert types[-1] == "done"
        start = events[0]
        assert start["model"] == "mistral"
        assert len(start["sources"]) == 3
        joined = "".join(e["text"] for e in events if e["type"] == "delta")
        assert joined == "Go ASUS!"
        done = events[-1]
        assert done["answer"] == "Go ASUS!"
        assert done["query"] == QUESTION["question"]
        assert done["elapsed_ms"] >= 0

    def test_stream_error_event_on_failure(self, rag_env, monkeypatch):
        def broken(*a, **kw):
            raise llm.LLMUnavailable("Ollama died mid-stream")
        monkeypatch.setattr(llm, "stream_chat", broken)
        res = client.post("/ask-ai/stream", json=QUESTION)
        assert res.status_code == 200  # headers already sent
        events = [json.loads(line) for line in res.text.strip().splitlines()]
        assert events[0]["type"] == "start"
        assert events[-1] == {"type": "error", "detail": "Ollama died mid-stream"}

    def test_stream_blank_question_rejected_before_streaming(self, rag_env, monkeypatch):
        res = client.post("/ask-ai/stream", json={"question": ""})
        assert res.status_code == 422

    def test_root_lists_ask_ai_endpoints(self):
        eps = client.get("/").json()["endpoints"]
        assert any("/ask-ai" in key for key in eps)
