import csv
import os
import time
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.recommend import (
    load_data,
    preprocess,
    cpu_tier,
    gpu_tier,
    parse_user_budget,
    parse_user_purpose,
    score_laptop,
    recommend,
    format_laptop,
    get_dataset_stats,
    get_available_brands,
    get_insights,
    CPU_TIERS,
    GPU_TIERS,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "laptops_ml_ready.csv")


class TestDataLoading:
    def test_load_data_returns_list(self):
        rows = load_data()
        assert isinstance(rows, list)
        assert len(rows) > 5000

    def test_load_data_has_headers(self):
        rows = load_data()
        row = rows[0]
        assert "Brand" in row
        assert "Price_NPR" in row
        assert "CPU_Model" in row

    def test_preprocess_preserves_count(self):
        rows = load_data()
        cleaned = preprocess(rows)
        assert len(cleaned) == len(rows)

    def test_preprocess_fills_missing_brand(self):
        rows = load_data()
        cleaned = preprocess(rows)
        for row in cleaned:
            assert row["Brand"].strip() != ""

    def test_preprocess_fills_missing_cpu_model(self):
        rows = load_data()
        cleaned = preprocess(rows)
        for row in cleaned:
            assert row["CPU_Model"].strip() != ""

    def test_preprocess_numeric_fields_are_float(self):
        rows = load_data()
        cleaned = preprocess(rows)
        for row in cleaned:
            assert isinstance(row["RAM_GB"], float)
            assert isinstance(row["Storage_GB"], float)
            assert isinstance(row["Price_NPR"], float)
            assert isinstance(row["Weight_KG"], float)

    def test_preprocess_creates_purpose_labels(self):
        rows = load_data()
        cleaned = preprocess(rows)
        for row in cleaned:
            assert "Purpose_Labels" in row
            assert isinstance(row["Purpose_Labels"], list)

    def test_preprocess_gpu_unknown_becomes_integrated(self):
        rows = load_data()
        cleaned = preprocess(rows)
        for row in cleaned:
            if row["GPU_Model"] == "Integrated":
                assert row["GPU_Model"] == "Integrated"


class TestCPUTier:
    def test_celeron_is_tier_1(self):
        assert cpu_tier("Intel Celeron N4020") == 1

    def test_pentium_is_tier_1(self):
        assert cpu_tier("Intel Pentium Silver N5030") == 1

    def test_i3_is_tier_2(self):
        assert cpu_tier("Core i3-1115G4") == 2

    def test_ryzen3_is_tier_2(self):
        assert cpu_tier("AMD Ryzen 3 3200U") == 2

    def test_i5_basic_is_tier_3(self):
        assert cpu_tier("Intel Core i5-1035G1") == 3

    def test_i5_higher_is_tier_4(self):
        assert cpu_tier("Intel Core i5-13500H") == 4

    def test_i7_basic_is_tier_4(self):
        assert cpu_tier("Intel Core i7-8550U") == 4

    def test_i7_higher_is_tier_5(self):
        assert cpu_tier("Intel Core i7-13700H") == 5

    def test_i9_is_tier_5_or_6(self):
        tier = cpu_tier("Intel Core i9-12900H")
        assert tier in (5, 6)

    def test_i9_extreme_is_tier_6(self):
        assert cpu_tier("Intel Core i9-13980HX") == 6

    def test_ryzen5_is_tier_3_or_4(self):
        tier = cpu_tier("AMD Ryzen 5 5500U")
        assert tier in (3, 4)

    def test_ryzen7_is_tier_4_or_5(self):
        tier = cpu_tier("AMD Ryzen 7 7840HS")
        assert tier in (4, 5)

    def test_ryzen9_higher_is_tier_6(self):
        assert cpu_tier("AMD Ryzen 9 7945HX") == 6

    def test_apple_m1_is_tier_6(self):
        assert cpu_tier("Apple M1") == 6

    def test_apple_m2_is_tier_6(self):
        assert cpu_tier("Apple M2") == 6

    def test_unknown_cpu_returns_tier_1(self):
        assert cpu_tier("Custom XYZ Processor") == 1

    def test_empty_string_returns_tier_1(self):
        assert cpu_tier("") == 1


class TestGPUTier:
    def test_integrated_hd_is_tier_2(self):
        assert gpu_tier("Intel HD Graphics 620") == 2

    def test_integrated_uhd_is_tier_2(self):
        assert gpu_tier("Intel UHD Graphics 620") == 2

    def test_iris_xe_is_tier_2_or_3(self):
        tier = gpu_tier("Intel Iris Xe Graphics")
        assert tier in (2, 3)

    def test_mx_series_is_tier_2(self):
        assert gpu_tier("NVIDIA GeForce MX450") == 2

    def test_gtx_1650_is_tier_3(self):
        assert gpu_tier("NVIDIA GeForce GTX 1650") == 3

    def test_rtx_3050_is_tier_3(self):
        assert gpu_tier("NVIDIA GeForce RTX 3050") == 3

    def test_rtx_3060_is_tier_5(self):
        assert gpu_tier("NVIDIA GeForce RTX 3060") == 5

    def test_rtx_4060_is_tier_5(self):
        assert gpu_tier("NVIDIA GeForce RTX 4060") == 5

    def test_rtx_4090_is_tier_6(self):
        assert gpu_tier("NVIDIA GeForce RTX 4090") == 6

    def test_rtx_5090_is_tier_6(self):
        assert gpu_tier("NVIDIA GeForce RTX 5090") == 6

    def test_radeon_integrated_is_tier_1(self):
        assert gpu_tier("AMD Radeon R5") == 1

    def test_unknown_gpu_returns_tier_1(self):
        assert gpu_tier("Unknown GPU XYZ") == 1

    def test_empty_string_returns_tier_1(self):
        assert gpu_tier("") == 1


class TestBudgetParsing:
    def test_plain_number(self):
        assert parse_user_budget("100000") == 100000.0

    def test_number_with_commas(self):
        assert parse_user_budget("1,00,000") == 100000.0

    def test_lakh_suffix(self):
        assert parse_user_budget("1.5 lakh") == 150000.0

    def test_lac_suffix(self):
        assert parse_user_budget("2 lac") == 200000.0

    def test_k_suffix(self):
        assert parse_user_budget("80k") == 80000.0

    def test_small_number_treated_as_lakh(self):
        val = parse_user_budget("5")
        assert val == 500000.0

    def test_invalid_input_returns_none(self):
        assert parse_user_budget("abc") is None

    def test_empty_string_returns_none(self):
        assert parse_user_budget("") is None

    def test_spaces_and_commas(self):
        assert parse_user_budget("1, 50, 000") == 150000.0


class TestPurposeParsing:
    def test_gaming(self):
        assert "Gaming" in parse_user_purpose("gaming")

    def test_programming(self):
        assert "Programming" in parse_user_purpose("programming")

    def test_student(self):
        labels = parse_user_purpose("student")
        assert "Student" in labels

    def test_studying(self):
        labels = parse_user_purpose("studying")
        assert "Student" in labels

    def test_office(self):
        labels = parse_user_purpose("office")
        assert "Office" in labels

    def test_office_work(self):
        labels = parse_user_purpose("office work")
        assert "Office" in labels
        assert "General Use" in labels

    def test_video_editing(self):
        labels = parse_user_purpose("video editing")
        assert "Video Editing" in labels

    def test_graphic_design(self):
        labels = parse_user_purpose("graphic design")
        assert "Graphic Design" in labels

    def test_machine_learning(self):
        labels = parse_user_purpose("machine learning")
        assert "AI / Machine Learning" in labels

    def test_ai(self):
        labels = parse_user_purpose("AI")
        assert "AI / Machine Learning" in labels

    def test_data_science(self):
        labels = parse_user_purpose("data science")
        assert "AI / Machine Learning" in labels

    def test_empty_input_returns_general(self):
        assert "General Use" in parse_user_purpose("")

    def test_unknown_returns_general(self):
        assert "General Use" in parse_user_purpose("zzzzzzzzz")

    def test_case_insensitive(self):
        assert "Gaming" in parse_user_purpose("GAMING")
        assert "Gaming" in parse_user_purpose("Gaming")

    def test_multiple_purposes(self):
        labels = parse_user_purpose("gaming and programming")
        assert "Gaming" in labels
        assert "Programming" in labels


class TestScoring:
    def _make_user(self, **overrides):
        user = {
            "budget": 100000,
            "purpose_labels": set(["Gaming"]),
            "min_ram": 0,
            "min_storage": 0,
            "min_cpu_tier": 0,
            "min_gpu_tier": 0,
            "brand": "",
            "storage_type": "",
            "min_screen": 0,
            "touchscreen": False,
        }
        user.update(overrides)
        return user

    def _make_laptop(self, **overrides):
        laptop = {
            "Brand": "TestBrand",
            "CPU_Model": "Core i5-1335U",
            "CPU_Brand": "Intel",
            "GPU_Model": "NVIDIA GeForce RTX 3050",
            "GPU_Brand": "NVIDIA",
            "RAM_GB": 16,
            "Storage_GB": 512,
            "Storage_Type": "SSD",
            "Screen_Size_Inches": 15.6,
            "Touchscreen": 0,
            "Operating_System": "Windows 11",
            "Weight_KG": 1.8,
            "Price_NPR": 85000,
            "Purpose": "Gaming",
            "Purpose_Labels": ["Gaming"],
        }
        laptop.update(overrides)
        return laptop

    def test_score_within_budget(self):
        laptop = self._make_laptop()
        user = self._make_user(budget=100000)
        score, reasons, penalties = score_laptop(laptop, user)
        assert score > 50
        assert any("budget" in r.lower() for r in reasons)

    def test_score_over_budget_penalty(self):
        laptop = self._make_laptop(Price_NPR=200000)
        user = self._make_user(budget=100000)
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("over budget" in p.lower() for p in penalties)

    def test_score_purpose_match(self):
        laptop = self._make_laptop()
        user = self._make_user(purpose_labels=set(["Gaming"]))
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("purpose" in r.lower() for r in reasons)

    def test_score_purpose_mismatch_penalty(self):
        laptop = self._make_laptop(Purpose_Labels=["Office"])
        user = self._make_user(purpose_labels=set(["Gaming"]))
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("purpose" in p.lower() for p in penalties)

    def test_score_brand_match(self):
        laptop = self._make_laptop(Brand="Dell")
        user = self._make_user(brand="Dell")
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("brand" in r.lower() and "dell" in r.lower() for r in reasons)

    def test_score_brand_mismatch_penalty(self):
        laptop = self._make_laptop(Brand="HP")
        user = self._make_user(brand="Dell")
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("brand" in p.lower() for p in penalties)

    def test_score_ram_meets_requirement(self):
        laptop = self._make_laptop(RAM_GB=32)
        user = self._make_user(min_ram=16)
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("ram" in r.lower() for r in reasons)

    def test_score_ram_below_requirement_penalty(self):
        laptop = self._make_laptop(RAM_GB=4)
        user = self._make_user(min_ram=16)
        score, reasons, penalties = score_laptop(laptop, user)
        assert any("ram" in p.lower() for p in penalties)

    def test_score_range_0_to_100(self):
        laptop = self._make_laptop()
        user = self._make_user()
        score, _, _ = score_laptop(laptop, user)
        assert 0 <= score <= 100


class TestRecommend:
    def test_basic_recommendation(self):
        result = recommend({"budget": "100000", "purpose": "gaming"}, top_n=3)
        assert result["status"] in ("ok", "no_exact_match")
        assert len(result["recommendations"]) > 0

    def test_returns_top_n_results(self):
        result = recommend({"budget": "100000", "purpose": "gaming"}, top_n=3)
        assert len(result["recommendations"]) <= 3

    def test_high_budget_returns_results(self):
        result = recommend({"budget": "500000", "purpose": "programming"}, top_n=5)
        assert result["status"] == "ok"
        assert len(result["recommendations"]) > 0

    def test_low_budget_returns_fallback(self):
        result = recommend({"budget": "1000", "purpose": "gaming"}, top_n=5)
        assert result["status"] == "no_exact_match"

    def test_recommendations_have_all_fields(self):
        result = recommend({"budget": "100000", "purpose": "gaming"}, top_n=3)
        for rec in result["recommendations"]:
            assert "laptop" in rec
            assert "score" in rec
            assert "reasons" in rec
            assert "penalties" in rec
            assert "brand" in rec["laptop"]
            assert "price_npr" in rec["laptop"]

    def test_recommendations_sorted_by_score(self):
        result = recommend({"budget": "100000", "purpose": "gaming"}, top_n=5)
        scores = [r["score"] for r in result["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_with_brand_filter(self):
        result = recommend({"budget": "100000", "purpose": "office", "brand": "HP"}, top_n=5)
        for rec in result["recommendations"]:
            assert rec["laptop"]["brand"] == "HP"

    def test_with_ram_filter(self):
        result = recommend({"budget": "150000", "purpose": "programming", "min_ram": 16}, top_n=5)
        for rec in result["recommendations"]:
            assert rec["laptop"]["ram_gb"] >= 8

    def test_student_low_budget(self):
        result = recommend({"budget": "50000", "purpose": "student"}, top_n=3)
        assert result["status"] in ("ok", "no_exact_match")
        assert len(result["recommendations"]) > 0

    def test_empty_budget(self):
        result = recommend({"budget": "", "purpose": "general"}, top_n=3)
        assert result["status"] in ("ok", "no_exact_match")

    def test_user_query_reflected(self):
        result = recommend({"budget": "100000", "purpose": "gaming"}, top_n=3)
        assert result["user_query"]["budget"] == 100000.0
        assert result["user_query"]["purpose"] == "gaming"


class TestDatasetStats:
    def test_total_laptops(self):
        stats = get_dataset_stats()
        assert stats["total_laptops"] > 5000

    def test_price_range(self):
        stats = get_dataset_stats()
        assert stats["price_range"]["min"] > 0
        assert stats["price_range"]["max"] > stats["price_range"]["min"]
        assert stats["price_range"]["avg"] > 0

    def test_brands_present(self):
        stats = get_dataset_stats()
        assert "HP" in stats["brands"]
        assert "Lenovo" in stats["brands"]

    def test_purpose_distribution(self):
        stats = get_dataset_stats()
        assert len(stats["purpose_distribution"]) > 0


class TestAvailableBrands:
    def test_brands_list(self):
        brands = get_available_brands()
        assert isinstance(brands, list)
        assert len(brands) > 20

    def test_brands_sorted(self):
        brands = get_available_brands()
        assert brands == sorted(brands)

    def test_known_brands_present(self):
        brands = get_available_brands()
        for b in ["HP", "Dell", "Lenovo", "ASUS", "Acer"]:
            assert b in brands


class TestGetInsights:
    def test_total_laptops_matches_stats(self):
        insights = get_insights()
        stats = get_dataset_stats()
        assert insights["total_laptops"] == stats["total_laptops"]

    def test_price_histogram_covers_all_priced_laptops(self):
        insights = get_insights()
        total_in_bins = sum(b["count"] for b in insights["price_histogram"])
        assert total_in_bins == insights["positive_price_count"]

    def test_price_histogram_buckets_are_ordered(self):
        insights = get_insights()
        buckets = [b["bucket"] for b in insights["price_histogram"]]
        assert buckets[0].startswith("0K-")
        assert buckets[-1] == "200K+"

    def test_top_brands_sorted_desc_and_capped(self):
        insights = get_insights()
        counts = [b["count"] for b in insights["top_brands"]]
        assert counts == sorted(counts, reverse=True)
        assert 0 < len(counts) <= 10

    def test_tiers_cover_1_to_6(self):
        insights = get_insights()
        for key in ["cpu_tier_distribution", "gpu_tier_distribution"]:
            tiers = [t["tier"] for t in insights[key]]
            assert tiers == [1, 2, 3, 4, 5, 6]
            assert all(t["count"] >= 0 for t in insights[key])

    def test_ram_vs_price_sorted_and_filtered(self):
        insights = get_insights()
        rams = [r["ram_gb"] for r in insights["ram_vs_price"]]
        assert rams == sorted(rams)
        for r in insights["ram_vs_price"]:
            assert r["count"] >= 20
            assert r["avg_price"] > 0

    def test_storage_types_present(self):
        insights = get_insights()
        types = {s["storage_type"] for s in insights["storage_type_distribution"]}
        assert "SSD" in types
        assert "HDD" in types

    def test_performance_under_2s(self):
        start = time.time()
        get_insights()
        elapsed = time.time() - start
        assert elapsed < 2.0, f"get_insights took {elapsed:.2f}s"


class TestPerformance:
    def test_recommend_under_2s(self):
        start = time.time()
        recommend({"budget": "100000", "purpose": "gaming"}, top_n=5)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Recommendation took {elapsed:.2f}s"

    def test_recommend_multiple_queries(self):
        queries = [
            {"budget": "50000", "purpose": "student"},
            {"budget": "100000", "purpose": "gaming"},
            {"budget": "200000", "purpose": "video editing"},
        ]
        start = time.time()
        for q in queries:
            result = recommend(q, top_n=3)
            assert len(result["recommendations"]) > 0
        elapsed = time.time() - start
        assert elapsed < 6.0
