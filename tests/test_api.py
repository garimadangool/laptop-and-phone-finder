import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestRootEndpoint:
    def test_root_returns_api_info(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Laptop Recommendation API"
        assert "endpoints" in data


class TestBrandsEndpoint:
    def test_brands_returns_list(self):
        resp = client.get("/brands")
        assert resp.status_code == 200
        data = resp.json()
        assert "brands" in data
        assert isinstance(data["brands"], list)
        assert len(data["brands"]) > 20

    def test_brands_contains_hp(self):
        resp = client.get("/brands")
        assert "HP" in resp.json()["brands"]


class TestPurposesEndpoint:
    def test_purposes_returns_list(self):
        resp = client.get("/purposes")
        assert resp.status_code == 200
        data = resp.json()
        assert "purposes" in data
        assert isinstance(data["purposes"], list)
        assert len(data["purposes"]) == 10

    def test_purposes_contains_gaming(self):
        resp = client.get("/purposes")
        assert "Gaming" in resp.json()["purposes"]


class TestStatsEndpoint:
    def test_stats_returns_data(self):
        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_laptops"] > 5000
        assert data["price_range"]["min"] > 0
        assert data["price_range"]["max"] > data["price_range"]["min"]

    def test_stats_has_brands(self):
        resp = client.get("/stats")
        assert "HP" in resp.json()["brands"]


class TestInsightsEndpoint:
    def test_insights_returns_data(self):
        resp = client.get("/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_laptops"] > 5000
        for key in [
            "price_histogram",
            "top_brands",
            "purpose_distribution",
            "ram_vs_price",
            "cpu_tier_distribution",
            "gpu_tier_distribution",
            "storage_type_distribution",
        ]:
            assert key in data
            assert len(data[key]) > 0

    def test_insights_price_histogram_sums(self):
        resp = client.get("/insights")
        data = resp.json()
        total_in_bins = sum(b["count"] for b in data["price_histogram"])
        assert total_in_bins == data["positive_price_count"]

    def test_insights_top_brands_sorted_desc(self):
        resp = client.get("/insights")
        counts = [b["count"] for b in resp.json()["top_brands"]]
        assert counts == sorted(counts, reverse=True)
        assert len(counts) <= 10

    def test_insights_tiers_cover_1_to_6(self):
        resp = client.get("/insights")
        data = resp.json()
        assert [t["tier"] for t in data["cpu_tier_distribution"]] == [1, 2, 3, 4, 5, 6]
        assert [t["tier"] for t in data["gpu_tier_distribution"]] == [1, 2, 3, 4, 5, 6]

    def test_insights_ram_sorted_with_min_count(self):
        resp = client.get("/insights")
        rams = [r["ram_gb"] for r in resp.json()["ram_vs_price"]]
        assert rams == sorted(rams)
        assert all(r["count"] >= 20 for r in resp.json()["ram_vs_price"])

    def test_root_lists_insights_endpoint(self):
        resp = client.get("/")
        assert "GET /insights" in resp.json()["endpoints"]


from fastapi.testclient import TestClient
from api.main import app
from api import interactions

client = TestClient(app)


@pytest.fixture()
def temp_log_db(tmp_path, monkeypatch):
    """Point interaction logging at a throwaway database per test."""
    interactions.set_db_path(str(tmp_path / "test_interactions.db"))
    yield
    interactions.set_db_path(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "interactions.db")
    )


class TestLoggingEndpoints:
    def test_log_search_returns_id(self, temp_log_db):
        resp = client.post("/log-search", json={
            "client_sid": "s-abc",
            "budget": "100000",
            "purpose": "gaming",
            "top_n": 12,
            "status": "ok",
            "results_shown": 12,
            "top_score": 97.7,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "logged"
        first = body["id"]
        second = client.post("/log-search", json={"budget": "50000", "purpose": "student"}).json()["id"]
        assert second > first

    def test_log_search_defaults(self, temp_log_db):
        resp = client.post("/log-search", json={})
        assert resp.status_code == 200

    def test_log_click_view_details(self, temp_log_db):
        search_id = client.post("/log-search", json={"budget": "80000"}).json()["id"]
        resp = client.post("/log-click", json={
            "action": "view_details",
            "client_sid": "s-abc",
            "search_row_id": search_id,
            "position": 2,
            "score": 88.4,
            "brand": "HP",
            "cpu_model": "Intel Core i5",
            "gpu_model": "RTX 3050",
            "ram_gb": 16,
            "price_npr": 79990,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged"

    def test_log_click_all_actions(self, temp_log_db):
        for action in ["view_details", "compare_add", "compare_remove", "show_more"]:
            resp = client.post("/log-click", json={"action": action})
            assert resp.status_code == 200

    def test_log_click_invalid_action_rejected(self, temp_log_db):
        resp = client.post("/log-click", json={"action": "delete_everything"})
        assert resp.status_code == 422

    def test_log_click_missing_action_rejected(self, temp_log_db):
        resp = client.post("/log-click", json={"brand": "Dell"})
        assert resp.status_code == 422

    def test_logs_stats_counts(self, temp_log_db):
        client.post("/log-search", json={"budget": "60000"})
        client.post("/log-click", json={"action": "view_details", "position": 0})
        client.post("/log-click", json={"action": "compare_add"})
        stats = client.get("/logs/stats").json()
        assert stats["total_searches"] >= 1
        assert stats["total_clicks"] >= 2
        assert stats["clicks_by_action"].get("view_details") == 1
        assert stats["clicks_by_action"].get("compare_add") == 1

    def test_root_lists_logging_endpoints(self):
        endpoints = client.get("/").json()["endpoints"]
        assert "POST /log-search" in endpoints
        assert "POST /log-click" in endpoints
        assert "GET /logs/stats" in endpoints


class TestRecommendEndpoint:
    def test_basic_recommendation(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "gaming",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "no_exact_match")
        assert len(data["recommendations"]) > 0

    def test_recommendation_with_all_filters(self):
        resp = client.post("/recommend", json={
            "budget": "150000",
            "purpose": "programming",
            "min_ram": 16,
            "min_storage": 512,
            "storage_type": "SSD",
            "brand": "HP",
            "top_n": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        for rec in data["recommendations"]:
            assert rec["laptop"]["brand"] == "HP"

    def test_recommendation_response_structure(self):
        resp = client.post("/recommend", json={
            "budget": "80000",
            "purpose": "office",
        })
        data = resp.json()
        assert "status" in data
        assert "message" in data
        assert "recommendations" in data
        assert "user_query" in data
        for rec in data["recommendations"]:
            assert "laptop" in rec
            assert "score" in rec
            assert "reasons" in rec
            assert "penalties" in rec

    def test_recommendation_scores_sorted(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "gaming",
            "top_n": 5,
        })
        scores = [r["score"] for r in resp.json()["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_missing_budget_returns_error(self):
        resp = client.post("/recommend", json={
            "purpose": "gaming",
        })
        assert resp.status_code == 422

    def test_missing_purpose_returns_error(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
        })
        assert resp.status_code == 422

    def test_empty_body_returns_error(self):
        resp = client.post("/recommend", json={})
        assert resp.status_code == 422

    def test_low_budget_returns_fallback(self):
        resp = client.post("/recommend", json={
            "budget": "3000",
            "purpose": "gaming",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no_exact_match"

    def test_high_budget_returns_results(self):
        resp = client.post("/recommend", json={
            "budget": "500000",
            "purpose": "video editing",
            "top_n": 5,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_top_n_limit(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "gaming",
            "top_n": 20,
        })
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) <= 20

    def test_negative_top_n_rejected(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "gaming",
            "top_n": -1,
        })
        assert resp.status_code == 422

    def test_purpose_student(self):
        resp = client.post("/recommend", json={
            "budget": "50000",
            "purpose": "student",
        })
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) > 0

    def test_purpose_ai_ml(self):
        resp = client.post("/recommend", json={
            "budget": "200000",
            "purpose": "AI / Machine Learning",
        })
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) > 0
