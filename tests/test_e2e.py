import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api.main import app
from model.recommend import recommend, get_dataset_stats, get_available_brands

client = TestClient(app)


class TestEndToEndPipeline:
    def test_ui_input_to_api_response(self):
        user_input = {
            "budget": "100000",
            "purpose": "gaming",
            "min_ram": 16,
            "min_storage": 512,
            "storage_type": "SSD",
            "brand": "",
            "min_screen": 0,
            "touchscreen": False,
            "top_n": 5,
        }
        result = recommend(user_input, top_n=5)
        assert result["status"] in ("ok", "no_exact_match")
        assert len(result["recommendations"]) > 0

        first_rec = result["recommendations"][0]
        assert "laptop" in first_rec
        assert "score" in first_rec
        assert first_rec["score"] > 0
        assert first_rec["laptop"]["brand"] != ""

    def test_api_matches_direct_model_call(self):
        payload = {
            "budget": "100000",
            "purpose": "gaming",
            "min_ram": 16,
            "top_n": 3,
        }
        api_resp = client.post("/recommend", json=payload)
        direct = recommend({
            "budget": "100000",
            "purpose": "gaming",
            "min_ram": 16,
            "min_storage": 0,
            "storage_type": "",
            "brand": "",
            "min_cpu_tier": 0,
            "min_gpu_tier": 0,
            "min_screen": 0,
            "touchscreen": False,
        }, top_n=3)
        assert api_resp.status_code == 200
        api_data = api_resp.json()
        assert len(api_data["recommendations"]) == len(direct["recommendations"])

    def test_all_purpose_variations_via_api(self):
        purposes = ["gaming", "programming", "office", "student",
                     "AI / Machine Learning", "video editing",
                     "graphic design", "heavy multitasking", "general"]
        for purpose in purposes:
            resp = client.post("/recommend", json={
                "budget": "100000",
                "purpose": purpose,
                "top_n": 3,
            })
            assert resp.status_code == 200, f"Failed for purpose: {purpose}"

    def test_budget_variations_via_api(self):
        budgets = ["30000", "50000", "100000", "150000",
                    "200000", "1.5 lakh", "2 lac", "80k"]
        for budget in budgets:
            resp = client.post("/recommend", json={
                "budget": budget,
                "purpose": "gaming",
                "top_n": 3,
            })
            assert resp.status_code == 200, f"Failed for budget: {budget}"

    def test_fallback_when_no_match(self):
        resp = client.post("/recommend", json={
            "budget": "1000",
            "purpose": "gaming",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no_exact_match"
        assert "Closest alternative" in data["recommendations"][0]["reasons"][0]

    def test_dataset_stats_consistent(self):
        stats_direct = get_dataset_stats()
        stats_api = client.get("/stats").json()
        assert stats_direct["total_laptops"] == stats_api["total_laptops"]

    def test_brands_consistent(self):
        brands_direct = get_available_brands()
        brands_api = client.get("/brands").json()["brands"]
        assert brands_direct == brands_api

    def test_full_pipeline_gaming_budget(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "gaming",
            "min_ram": 16,
            "min_storage": 512,
            "storage_type": "SSD",
            "top_n": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["user_query"]["budget"] == 100000.0
        for rec in data["recommendations"]:
            lt = rec["laptop"]
            assert lt["ram_gb"] >= 8
            assert rec["score"] > 50

    def test_full_pipeline_student_low_budget(self):
        resp = client.post("/recommend", json={
            "budget": "40000",
            "purpose": "student",
            "top_n": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        for rec in data["recommendations"]:
            assert rec["laptop"]["price_npr"] <= 60000

    def test_brand_filter_end_to_end(self):
        resp = client.post("/recommend", json={
            "budget": "100000",
            "purpose": "office",
            "brand": "Dell",
            "top_n": 5,
        })
        assert resp.status_code == 200
        for rec in resp.json()["recommendations"]:
            assert rec["laptop"]["brand"] == "Dell"
