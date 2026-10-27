from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api import interactions
from model import rag
from model import llm
from model.recommend import (
    recommend,
    get_dataset_stats,
    get_available_brands,
    get_insights,
    ALL_PURPOSE_LABELS,
)
from model.recommend_phones import (
    recommend_phones,
    get_phone_stats,
    get_phone_insights,
    ALL_PHONE_PURPOSES,
)
from model import rag_phones

app = FastAPI(
    title="Laptop Recommendation API",
    description="Get ranked laptop recommendations based on your budget, purpose, and specs.",
    version="1.0.0",
)

# Allow the React frontend (Vite dev server / local builds) to call this API
# directly when it is not served through the Vite proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://localhost:3000",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    budget: str = Field(..., description="Your budget (e.g. '100000', '1.5 lakh', '80k')")
    purpose: str = Field(..., description="What you need the laptop for (e.g. 'gaming', 'programming', 'video editing')")
    min_ram: Optional[float] = Field(None, description="Minimum RAM in GB (e.g. 8, 16)")
    min_storage: Optional[float] = Field(None, description="Minimum storage in GB (e.g. 256, 512, 1000)")
    storage_type: Optional[str] = Field(None, description="Storage type preference (e.g. 'SSD', 'HDD', 'any')")
    brand: Optional[str] = Field(None, description="Preferred brand (e.g. 'Dell', 'HP', 'ASUS')")
    min_cpu_tier: Optional[int] = Field(None, ge=1, le=6, description="Minimum CPU tier 1-6 (1=budget, 6=workstation)")
    min_gpu_tier: Optional[int] = Field(None, ge=1, le=6, description="Minimum GPU tier 1-6 (1=integrated, 6=high-end)")
    min_screen: Optional[float] = Field(None, description="Minimum screen size in inches")
    touchscreen: Optional[bool] = Field(False, description="Require touchscreen")
    dedicated_gpu: Optional[bool] = Field(False, description="Require dedicated GPU (exclude integrated graphics)")
    top_n: Optional[int] = Field(5, ge=1, le=20, description="Number of recommendations to return")


class LaptopOut(BaseModel):
    brand: str
    cpu_model: str
    cpu_brand: str
    cpu_tier: int
    gpu_model: str
    gpu_brand: str
    gpu_tier: int
    ram_gb: float
    storage_gb: float
    storage_type: str
    screen_size: float
    touchscreen: bool
    os: str
    weight_kg: float
    price_npr: float
    purpose: str


class DealOut(BaseModel):
    is_deal: bool
    tier: str
    note: str


class Recommendation(BaseModel):
    laptop: LaptopOut
    score: float
    reasons: List[str]
    penalties: List[str]
    deal: DealOut = None


class RecommendResponse(BaseModel):
    status: str
    message: str
    recommendations: List[Recommendation]
    user_query: dict


class PriceRange(BaseModel):
    min: float
    max: float
    avg: float


class DatasetStatsResponse(BaseModel):
    total_laptops: int
    brands: dict
    purpose_distribution: dict
    price_range: PriceRange


class Bucket(BaseModel):
    bucket: str
    count: int


class BrandCount(BaseModel):
    brand: str
    count: int


class PurposeCount(BaseModel):
    purpose: str
    count: int


class RamPrice(BaseModel):
    ram_gb: int
    avg_price: float
    count: int


class TierCount(BaseModel):
    tier: int
    count: int


class StorageTypeCount(BaseModel):
    storage_type: str
    count: int


class InsightsResponse(BaseModel):
    total_laptops: int
    positive_price_count: int
    price_histogram: List[Bucket]
    top_brands: List[BrandCount]
    purpose_distribution: List[PurposeCount]
    ram_vs_price: List[RamPrice]
    cpu_tier_distribution: List[TierCount]
    gpu_tier_distribution: List[TierCount]
    storage_type_distribution: List[StorageTypeCount]


class LogSearchRequest(BaseModel):
    client_sid: Optional[str] = Field(None, max_length=64)
    budget: str = ""
    purpose: str = ""
    min_ram: Optional[float] = None
    min_storage: Optional[float] = None
    storage_type: Optional[str] = None
    brand: Optional[str] = None
    min_cpu_tier: Optional[int] = None
    min_gpu_tier: Optional[int] = None
    min_screen: Optional[float] = None
    touchscreen: bool = False
    dedicated_gpu: bool = False
    top_n: Optional[int] = None
    status: str = ""
    results_shown: int = 0
    top_score: Optional[float] = None


class LogClickRequest(BaseModel):
    action: Literal["view_details", "compare_add", "compare_remove", "show_more"]
    client_sid: Optional[str] = Field(None, max_length=64)
    search_row_id: Optional[int] = None
    position: Optional[int] = Field(None, ge=0)
    score: Optional[float] = None
    brand: Optional[str] = None
    cpu_model: Optional[str] = None
    gpu_model: Optional[str] = None
    ram_gb: Optional[float] = None
    storage_gb: Optional[float] = None
    storage_type: Optional[str] = None
    price_npr: Optional[float] = None
    os: Optional[str] = None
    screen_size: Optional[float] = None


class LogResponse(BaseModel):
    status: str
    id: int


class AskAnswer(BaseModel):
    rank: int
    similarity: float
    distance: float
    laptop: LaptopOut
    document: str = Field(..., description="Indexed spec-sheet text for this laptop (grounding source)")


class AskResponse(BaseModel):
    status: str
    message: str
    query: str
    total_indexed: int
    max_price_applied: Optional[float] = Field(None, description="Price cap auto-extracted from the query or passed explicitly")
    answers: List[AskAnswer]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class AskAiRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="User's question for the assistant")
    history: List[ChatTurn] = Field(default_factory=list, description="Previous chat turns (oldest first)")
    top_n: int = Field(5, ge=1, le=10, description="How many laptops to retrieve as grounding context")
    max_price: Optional[float] = Field(None, description="Optional price cap in NPR (overrides a budget phrase in the question)")
    brand: Optional[str] = Field(None, description="Optional brand filter")
    laptop: Optional[dict] = Field(None, description="The laptop the user is currently viewing (focus context)")


class AskAiSource(BaseModel):
    rank: int
    similarity: float
    laptop: LaptopOut
    document: str


class AskAiResponse(BaseModel):
    status: str
    answer: str
    model: str
    query: str
    retrieved: int
    sources: List[AskAiSource]
    elapsed_ms: int


@app.get("/")
def root():
    return {
        "name": "Laptop & Phone Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "POST /recommend": "Get laptop recommendations",
            "GET /brands": "List available laptop brands",
            "GET /purposes": "List available laptop purpose labels",
            "GET /stats": "Laptop dataset statistics",
            "GET /insights": "Laptop dataset insights for visualization",
            "GET /ask": "Laptop RAG retrieval",
            "POST /ask-ai": "Laptop AI chatbot",
            "POST /ask-ai/stream": "Laptop AI streaming",
            "POST /phones/recommend": "Get phone recommendations",
            "GET /phones/brands": "List phone brands",
            "GET /phones/purposes": "List phone purpose labels",
            "GET /phones/stats": "Phone dataset statistics",
            "GET /phones/insights": "Phone dataset insights",
            "GET /phones/ask": "Phone RAG retrieval",
            "POST /phones/ask-ai": "Phone AI chatbot",
            "POST /phones/ask-ai/stream": "Phone AI streaming",
            "POST /log-search": "Log a search",
            "POST /log-click": "Log a user interaction",
            "GET /logs/stats": "Interaction logging summary",
            "GET /docs": "Interactive API documentation",
        },
    }


@app.post("/recommend", response_model=RecommendResponse)
def get_recommendations(req: RecommendRequest):
    user_input = {
        "budget": req.budget,
        "purpose": req.purpose,
        "min_ram": req.min_ram or 0,
        "min_storage": req.min_storage or 0,
        "storage_type": req.storage_type or "",
        "brand": req.brand or "",
        "min_cpu_tier": req.min_cpu_tier or 0,
        "min_gpu_tier": req.min_gpu_tier or 0,
        "min_screen": req.min_screen or 0,
        "touchscreen": req.touchscreen or False,
        "dedicated_gpu": req.dedicated_gpu or False,
    }
    result = recommend(user_input, top_n=req.top_n or 5)
    return result


@app.get("/brands")
def list_brands():
    return {"brands": get_available_brands()}


@app.get("/purposes")
def list_purposes():
    return {"purposes": ALL_PURPOSE_LABELS}


@app.get("/stats", response_model=DatasetStatsResponse)
def dataset_stats():
    return get_dataset_stats()


@app.get("/insights", response_model=InsightsResponse)
def dataset_insights():
    return get_insights()


@app.get("/ask", response_model=AskResponse)
def ask_question(
    query: str = Query(..., min_length=1, description="Free-text question, e.g. 'gaming laptop under 100k'"),
    top_n: int = Query(5, ge=1, le=20, description="Number of laptops to retrieve"),
    max_price: Optional[float] = Query(None, description="Optional hard price cap in NPR (overrides a budget phrase in the query)"),
    brand: Optional[str] = Query(None, description="Optional brand filter (e.g. 'ASUS')"),
):
    """RAG retrieval: free-text question -> most relevant REAL laptops from the dataset.

    Answers are grounded by construction - every laptop comes from the indexed
    dataset, so prices/models can never be hallucinated.
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        return rag.ask(query=query.strip(), n_results=top_n, max_price=max_price, brand=brand)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _retrieve_for_askai(req: AskAiRequest):
    """Shared RAG retrieval + validation for both /ask-ai endpoints."""
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")
    try:
        return rag.ask(
            query=question,
            n_results=req.top_n,
            max_price=req.max_price,
            brand=req.brand,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _ask_ai_sources(retrieval):
    return [
        {"rank": ans["rank"], "similarity": ans["similarity"], "laptop": ans["laptop"], "document": ans["document"]}
        for ans in retrieval["answers"]
    ]


@app.post("/ask-ai", response_model=AskAiResponse)
def ask_ai(req: AskAiRequest):
    """Grounded LLM answer: question -> RAG retrieval -> Ollama explains the results.

    The LLM only ever describes laptops returned by retrieval from our own
    dataset; it is never allowed to invent models or prices.
    """
    started = time.perf_counter()
    retrieval = _retrieve_for_askai(req)
    sources = _ask_ai_sources(retrieval)

    if not sources:
        raise HTTPException(status_code=503, detail=retrieval["message"])

    focus = req.laptop if isinstance(req.laptop, dict) and req.laptop else None
    messages = llm.build_chat_messages(req.question.strip(), sources, history=[t.model_dump() for t in req.history], focus_laptop=focus)
    try:
        answer = llm.chat(messages, options=llm.default_options())
    except llm.LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "status": "ok",
        "answer": answer,
        "model": llm.model_name(),
        "query": req.question.strip(),
        "retrieved": len(sources),
        "sources": sources,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


@app.post("/ask-ai/stream")
def ask_ai_stream(req: AskAiRequest):
    """Streaming variant of /ask-ai.

    Emits newline-delimited JSON events: {"type":"delta","text":"..."} chunks
    followed by a final {"type":"done", ...} event carrying the cited sources.
    Retrieval and validation happen before the stream starts so HTTP errors are
    still reported normally.
    """
    started = time.perf_counter()
    retrieval = _retrieve_for_askai(req)
    sources = _ask_ai_sources(retrieval)

    if not sources:
        raise HTTPException(status_code=503, detail=retrieval["message"])

    focus = req.laptop if isinstance(req.laptop, dict) and req.laptop else None
    messages = llm.build_chat_messages(req.question.strip(), sources, history=[t.model_dump() for t in req.history], focus_laptop=focus)

    def event_stream():
        yield (
            json.dumps({"type": "start", "model": llm.model_name(), "sources": sources}) + "\n"
        )
        chunks = []
        try:
            for delta in llm.stream_chat(messages, options=llm.default_options()):
                chunks.append(delta)
                yield json.dumps({"type": "delta", "text": delta}) + "\n"
            yield json.dumps({
                "type": "done",
                "answer": "".join(chunks).strip(),
                "model": llm.model_name(),
                "query": req.question.strip(),
                "retrieved": len(sources),
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
            }) + "\n"
        except llm.LLMUnavailable as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


# ──────────────────────────────────────────────────────────────────────
# Phone endpoints
# ──────────────────────────────────────────────────────────────────────


class PhoneRecommendRequest(BaseModel):
    budget: str = Field(..., description="Your budget (e.g. '20000', '50k', '1.5 lakh')")
    purpose: str = Field(..., description="What you need the phone for (e.g. 'camera', 'gaming', 'student')")
    min_ram: Optional[float] = Field(None, description="Minimum RAM in GB")
    min_storage: Optional[float] = Field(None, description="Minimum storage in GB")
    brand: Optional[str] = Field(None, description="Preferred brand (e.g. 'Samsung', 'Xiaomi')")
    min_chipset_tier: Optional[int] = Field(None, ge=1, le=6, description="Minimum chipset tier 1-6")
    min_camera_mp: Optional[int] = Field(None, description="Minimum rear camera MP")
    min_battery: Optional[int] = Field(None, description="Minimum battery capacity in mAh")
    require_5g: Optional[bool] = Field(False, description="Require 5G support")
    require_nfc: Optional[bool] = Field(False, description="Require NFC")
    require_fingerprint: Optional[bool] = Field(False, description="Require fingerprint sensor")
    top_n: Optional[int] = Field(5, ge=1, le=20)


class PhoneOut(BaseModel):
    brand: str
    product_name: str
    chipset: str
    chipset_family: str
    chipset_tier: int
    gpu: str
    ram_gb: float
    storage_gb: float
    storage_type: str
    display_size: float
    display_type: str
    battery_mah: float
    fast_charging_w: float
    rear_camera_mp: float
    front_camera_mp: float
    has_ois: str
    has_5g: str
    has_nfc: str
    has_fingerprint: str
    weight_grams: float
    os: str
    price_npr: float
    original_price: float
    purpose: str


class PhoneRecommendation(BaseModel):
    laptop: PhoneOut
    score: float
    reasons: List[str]
    penalties: List[str]
    deal: DealOut = None


class PhoneRecommendResponse(BaseModel):
    status: str
    message: str
    recommendations: List[PhoneRecommendation]
    user_query: dict


class PhoneDatasetStatsResponse(BaseModel):
    total_phones: int
    brands: dict
    purpose_distribution: dict
    price_range: PriceRange


class PhoneInsightsResponse(BaseModel):
    total_phones: int
    positive_price_count: int
    price_histogram: List[Bucket]
    top_brands: List[BrandCount]
    purpose_distribution: List[PurposeCount]
    chipset_tier_distribution: List[TierCount]
    chipset_family_distribution: List[dict]
    camera_distribution: List[dict]
    fiveg_count: int
    nfc_count: int


class PhoneAskAnswer(BaseModel):
    rank: int
    similarity: float
    distance: float
    laptop: PhoneOut
    document: str


class PhoneAskResponse(BaseModel):
    status: str
    message: str
    query: str
    total_indexed: int
    max_price_applied: Optional[float]
    answers: List[PhoneAskAnswer]


class PhoneAskAiResponse(BaseModel):
    status: str
    answer: str
    model: str
    query: str
    retrieved: int
    sources: List[PhoneAskAnswer]
    elapsed_ms: int


@app.post("/phones/recommend", response_model=PhoneRecommendResponse)
def get_phone_recommendations(req: PhoneRecommendRequest):
    user_input = {
        "budget": req.budget,
        "purpose": req.purpose,
        "min_ram": req.min_ram or 0,
        "min_storage": req.min_storage or 0,
        "brand": req.brand or "",
        "min_chipset_tier": req.min_chipset_tier or 0,
        "min_camera_mp": req.min_camera_mp or 0,
        "min_battery": req.min_battery or 0,
        "require_5g": req.require_5g or False,
        "require_nfc": req.require_nfc or False,
        "require_fingerprint": req.require_fingerprint or False,
    }
    result = recommend_phones(user_input, top_n=req.top_n or 5)
    return result


@app.get("/phones/brands")
def list_phone_brands():
    phones = rag_phones.preprocess(rag_phones.load_data())
    brands = sorted(set(ph["Brand"] for ph in phones))
    return {"brands": brands}


@app.get("/phones/purposes")
def list_phone_purposes():
    return {"purposes": ALL_PHONE_PURPOSES}


@app.get("/phones/stats", response_model=PhoneDatasetStatsResponse)
def phone_dataset_stats():
    return get_phone_stats()


@app.get("/phones/insights", response_model=PhoneInsightsResponse)
def phone_dataset_insights():
    return get_phone_insights()


@app.get("/phones/ask", response_model=PhoneAskResponse)
def phone_ask_question(
    query: str = Query(..., min_length=1),
    top_n: int = Query(5, ge=1, le=20),
    max_price: Optional[float] = Query(None),
    brand: Optional[str] = Query(None),
):
    if not query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        return rag_phones.ask(query=query.strip(), n_results=top_n, max_price=max_price, brand=brand)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _retrieve_for_phone_askai(req: AskAiRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")
    try:
        return rag_phones.ask(
            query=question, n_results=req.top_n,
            max_price=req.max_price, brand=req.brand,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/phones/ask-ai", response_model=PhoneAskAiResponse)
def phone_ask_ai(req: AskAiRequest):
    started = time.perf_counter()
    retrieval = _retrieve_for_phone_askai(req)
    sources = [
        {"rank": a["rank"], "similarity": a["similarity"], "laptop": a["laptop"], "document": a["document"]}
        for a in retrieval["answers"]
    ]
    if not sources:
        raise HTTPException(status_code=503, detail=retrieval["message"])
    focus = req.laptop if isinstance(req.laptop, dict) and req.laptop else None
    messages = llm.build_chat_messages(req.question.strip(), sources, history=[t.model_dump() for t in req.history], focus_laptop=focus)
    try:
        answer = llm.chat(messages, options=llm.default_options())
    except llm.LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {
        "status": "ok", "answer": answer, "model": llm.model_name(),
        "query": req.question.strip(), "retrieved": len(sources),
        "sources": sources, "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


@app.post("/phones/ask-ai/stream")
def phone_ask_ai_stream(req: AskAiRequest):
    started = time.perf_counter()
    retrieval = _retrieve_for_phone_askai(req)
    sources = [
        {"rank": a["rank"], "similarity": a["similarity"], "laptop": a["laptop"], "document": a["document"]}
        for a in retrieval["answers"]
    ]
    if not sources:
        raise HTTPException(status_code=503, detail=retrieval["message"])
    focus = req.laptop if isinstance(req.laptop, dict) and req.laptop else None
    messages = llm.build_chat_messages(req.question.strip(), sources, history=[t.model_dump() for t in req.history], focus_laptop=focus)

    def event_stream():
        yield json.dumps({"type": "start", "model": llm.model_name(), "sources": sources}) + "\n"
        chunks = []
        try:
            for delta in llm.stream_chat(messages, options=llm.default_options()):
                chunks.append(delta)
                yield json.dumps({"type": "delta", "text": delta}) + "\n"
            yield json.dumps({
                "type": "done", "answer": "".join(chunks).strip(),
                "model": llm.model_name(), "query": req.question.strip(),
                "retrieved": len(sources),
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
            }) + "\n"
        except llm.LLMUnavailable as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


# ──────────────────────────────────────────────────────────────────────
# Interaction logging
# ──────────────────────────────────────────────────────────────────────


@app.post("/log-search", response_model=LogResponse)
def log_search(req: LogSearchRequest):
    row_id = interactions.insert_search(
        client_sid=req.client_sid,
        budget=req.budget,
        purpose=req.purpose,
        min_ram=req.min_ram,
        min_storage=req.min_storage,
        storage_type=req.storage_type,
        brand=req.brand,
        min_cpu_tier=req.min_cpu_tier,
        min_gpu_tier=req.min_gpu_tier,
        min_screen=req.min_screen,
        touchscreen=req.touchscreen,
        dedicated_gpu=req.dedicated_gpu,
        top_n=req.top_n,
        status=req.status,
        results_shown=req.results_shown,
        top_score=req.top_score,
    )
    return {"status": "logged", "id": row_id}


@app.post("/log-click", response_model=LogResponse)
def log_click(req: LogClickRequest):
    row_id = interactions.insert_click(client_sid=req.client_sid, **req.model_dump(exclude={"client_sid"}))
    return {"status": "logged", "id": row_id}


@app.get("/logs/stats")
def logs_stats():
    return interactions.log_stats()
