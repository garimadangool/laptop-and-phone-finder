import sys
import os
import csv
from collections import Counter
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api.main import app
from model import rag
from model.recommend import load_data, preprocess, cpu_tier


client = TestClient(app)


N_INDEX_ROWS = 150


def _slice_csv(dest_path, step=35):
    """Write a representative slice of the real dataset to a temp CSV."""
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
    """Build one small persisted index shared by this module's tests."""
    work = tmp_path_factory.mktemp("rag")
    csv_path, n_rows = _slice_csv(str(work / "slice.csv"))
    index_dir = str(work / "chroma")
    meta = rag.build_index(data_path=csv_path, persist_dir=index_dir)
    rag.set_index_dir(index_dir)
    yield {
        "index_dir": index_dir,
        "csv_path": csv_path,
        "n_rows": n_rows,
        "meta": meta,
    }
    rag.reset_index_dir()


class TestBudgetHint:
    def test_under_k(self):
        assert rag.extract_budget_hint("good gaming laptop under 80k") == 80000

    def test_below_lakh(self):
        assert rag.extract_budget_hint("lightweight laptop below 1 lakh") == 100000

    def test_budget_of_plain_number(self):
        assert rag.extract_budget_hint("office laptop with budget of 45000") == 45000

    def test_bare_small_number_means_k(self):
        assert rag.extract_budget_hint("cheap laptop under 60 for college") == 60000

    def test_thousand_suffix(self):
        assert rag.extract_budget_hint("laptop up to 50 thousand rupees") == 50000

    def test_no_price_phrase(self):
        assert rag.extract_budget_hint("best macbook for video editing") is None


class TestDocumentBuilder:
    def test_document_contains_brand_and_cpu(self):
        lt = preprocess(load_data())[0]
        doc = rag.build_document(lt)
        assert lt["Brand"].lower() in doc.lower()
        assert lt["CPU_Model"].lower().split()[0] in doc.lower()

    def test_document_contains_tier_and_price_words(self):
        lt = preprocess(load_data())[2]
        doc = rag.build_document(lt)
        assert f"tier {cpu_tier(lt['CPU_Model'])} of 6" in doc
        assert "npr" in doc.lower()
        assert "suited for" in doc

    def test_document_handles_unknown_weight_and_storage(self):
        lt = dict(preprocess(load_data())[0])
        lt["Weight_KG"] = 0.0
        lt["Storage_GB"] = 0.0
        doc = rag.build_document(lt)
        assert "weighs" not in doc
        assert "storage capacity not listed" in doc


class TestIndexBuilding:
    def test_build_reports_row_count(self, rag_env):
        assert rag_env["meta"]["count"] == rag_env["n_rows"]

    def test_meta_file_written(self, rag_env):
        import json
        with open(os.path.join(rag_env["index_dir"], "index_meta.json")) as f:
            meta = json.load(f)
        assert meta["count"] == rag_env["n_rows"]
        assert meta["collection"] == "laptops"
        assert meta["dimension"] > 0
        assert meta["built_at"]

    def test_rebuild_is_idempotent(self, rag_env):
        meta = rag.build_index(data_path=rag_env["csv_path"], persist_dir=rag_env["index_dir"])
        assert meta["count"] == rag_env["n_rows"]
        collection, _ = rag._load_index()
        assert collection.count() == rag_env["n_rows"]

    def test_missing_index_raises_helpful_error(self, tmp_path):
        previous = rag.INDEX_DIR
        rag.set_index_dir(str(tmp_path / "does_not_exist"))
        try:
            with pytest.raises(FileNotFoundError, match="python3 -m model.rag"):
                rag.ask("gaming laptop")
        finally:
            rag.set_index_dir(previous)


class TestAskRetrieval:
    def test_basic_gaming_query(self, rag_env):
        res = rag.ask("gaming laptop with dedicated RTX graphics", n_results=5)
        assert res["status"] == "ok"
        assert res["total_indexed"] == rag_env["n_rows"]
        assert len(res["answers"]) == 5
        assert [a["rank"] for a in res["answers"]] == [1, 2, 3, 4, 5]

    def test_similarity_sorted_descending(self, rag_env):
        sims = [a["similarity"] for a in rag.ask("cheap student laptop", n_results=6)["answers"]]
        assert sims == sorted(sims, reverse=True)

    def test_answers_grounded_in_dataset(self, rag_env):
        """Every answer must be a real row from the source CSV - no invention."""
        with open(rag_env["csv_path"]) as f:
            known = {(r["Brand"], float(r["Price_NPR"])) for r in csv.DictReader(f)}
        res = rag.ask("powerful workstation laptop", n_results=8)
        for ans in res["answers"]:
            key = (ans["laptop"]["brand"], float(ans["laptop"]["price_npr"]))
            assert key in known
            assert ans["document"], "document must be present for LLM grounding"

    def test_max_price_filter_respected(self, rag_env):
        res = rag.ask("any decent laptop", n_results=10, max_price=60000)
        assert res["max_price_applied"] == 60000
        for ans in res["answers"]:
            assert ans["laptop"]["price_npr"] <= 60000

    def test_brand_filter_respected(self, rag_env):
        res = rag.ask("solid reliable laptop", n_results=10, brand="HP")
        assert len(res["answers"]) > 0
        for ans in res["answers"]:
            assert ans["laptop"]["brand"] == "HP"

    def test_budget_hint_applied_from_query_text(self, rag_env):
        res = rag.ask("gaming laptop under 60k", n_results=5)
        assert res["max_price_applied"] == 60000
        for ans in res["answers"]:
            assert ans["laptop"]["price_npr"] <= 60000

    def test_explicit_filter_overrides_hint(self, rag_env):
        res = rag.ask("gaming laptop under 60k", n_results=5, max_price=30000)
        assert res["max_price_applied"] == 30000
        for ans in res["answers"]:
            assert ans["laptop"]["price_npr"] <= 30000

    def test_impossible_filters_give_no_match(self, rag_env):
        res = rag.ask("ultrabook", n_results=5, max_price=1)
        assert res["status"] == "no_match"
        assert res["answers"] == []

    def test_empty_query_rejected(self, rag_env):
        with pytest.raises(ValueError):
            rag.ask("   ")

    def test_n_results_clamped_to_collection_size(self, rag_env):
        res = rag.ask("laptop", n_results=9999)
        assert len(res["answers"]) <= rag_env["n_rows"]
        assert len(res["answers"]) <= 20


# ---------------------------------------------------------------------------
# API integration (GET /ask)
# ---------------------------------------------------------------------------

client = TestClient(app := __import__("api.main", fromlist=["app"]).app)


class TestAskEndpoint:
    def test_ask_returns_grounded_answers(self, rag_env):
        resp = client.get("/ask", params={"query": "gaming laptop under 80k", "top_n": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["query"] == "gaming laptop under 80k"
        assert data["total_indexed"] == rag_env["n_rows"]
        assert len(data["answers"]) == 3
        first = data["answers"][0]
        for key in ("rank", "similarity", "distance", "laptop", "document"):
            assert key in first
        assert first["rank"] == 1
        assert first["laptop"]["price_npr"] <= 80000

    def test_ask_missing_query_422(self, rag_env):
        resp = client.get("/ask")
        assert resp.status_code == 422

    def test_ask_whitespace_query_422(self, rag_env):
        resp = client.get("/ask", params={"query": "   "})
        assert resp.status_code == 422

    def test_ask_top_n_out_of_range_422(self, rag_env):
        resp = client.get("/ask", params={"query": "laptop", "top_n": 50})
        assert resp.status_code == 422

    def test_ask_503_when_index_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rag, "INDEX_DIR", str(tmp_path / "empty"))
        resp = client.get("/ask", params={"query": "gaming laptop"})
        assert resp.status_code == 503
        assert "python3 -m model.rag" in resp.json()["detail"]

    def test_root_lists_ask_endpoint(self):
        endpoints = client.get("/").json()["endpoints"]
        assert "GET /ask" in endpoints
