from __future__ import annotations

from typing import Any, Dict, List, Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from app.agents.concierge import SearchSchema, generate_search_schema
from app.agents.hunter import UniversalHunter
from app.agents.leadbuilder import FinalLeadProfile, LeadBuilder
from app.agents.scout import RawEvent, SignalScout
from app.agents.signal import SignalEngine, SignalInference
from app.agents.truthverify import TruthVerifier, VerifiedLead


app = FastAPI(title="Lead-Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str = "ok"


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


# -----------------------
# Concierge
# -----------------------
class ConciergePlanRequest(BaseModel):
    user_query: str = Field(min_length=1)


@app.post("/api/concierge/plan", response_model=SearchSchema)
async def concierge_plan(req: ConciergePlanRequest) -> SearchSchema:
    try:
        return generate_search_schema(req.user_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# Scout (Tavily)
# -----------------------
class ScoutSearchRequest(BaseModel):
    queries: List[str] = Field(min_length=1)


class ScoutSearchResponse(BaseModel):
    events: List[RawEvent]


@app.post("/api/scout/search", response_model=ScoutSearchResponse)
async def scout_search(req: ScoutSearchRequest) -> ScoutSearchResponse:
    try:
        scout = SignalScout()
        events = await scout.run(req.queries)
        return ScoutSearchResponse(events=events)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# Signal (Claude)
# -----------------------
class SignalInferRequest(BaseModel):
    industry: str = Field(min_length=1)
    raw_event: str = Field(min_length=1)
    event_date: Optional[str] = None


@app.post("/api/signal/infer", response_model=SignalInference)
async def signal_infer(req: SignalInferRequest) -> SignalInference:
    try:
        engine = SignalEngine()
        return await engine.process_raw_data(req.industry, req.raw_event, req.event_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# Hunter (Firecrawl)
# -----------------------
class HunterExtractRequest(BaseModel):
    url: str = Field(min_length=3)


class HunterExtractResponse(BaseModel):
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


@app.post("/api/hunter/extract", response_model=HunterExtractResponse)
async def hunter_extract(req: HunterExtractRequest) -> HunterExtractResponse:
    try:
        hunter = UniversalHunter()
        result = await hunter.run(req.url)
        return HunterExtractResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# TruthVerify (ZeroBounce + Proxycurl)
# -----------------------
class TruthVerifyRequest(BaseModel):
    company_name: str
    owner_name: Optional[str] = None
    email: Optional[str] = None


@app.post("/api/truthverify/run", response_model=VerifiedLead)
async def truthverify_run(req: TruthVerifyRequest) -> VerifiedLead:
    try:
        verifier = TruthVerifier()
        return await verifier.run(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# LeadBuilder
# -----------------------
class LeadBuilderRequest(BaseModel):
    signal_plan: Dict[str, Any]
    verified_info: Dict[str, Any]


@app.post("/api/leadbuilder/build", response_model=FinalLeadProfile)
async def leadbuilder_build(req: LeadBuilderRequest) -> FinalLeadProfile:
    try:
        builder = LeadBuilder()
        return await builder.run(req.signal_plan, req.verified_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# End-to-end pipeline (minimal wiring)
# -----------------------
class PipelineRunRequest(BaseModel):
    user_query: str = Field(min_length=1)
    max_events: int = 10
    max_hunter: int = 5


class PipelineRunResponse(BaseModel):
    plan: SearchSchema
    events: List[RawEvent]
    inferences: List[SignalInference] = Field(default_factory=list)
    extracted: List[HunterExtractResponse] = Field(default_factory=list)


@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
async def pipeline_run(req: PipelineRunRequest) -> PipelineRunResponse:
    """
    Minimal "connect everything" route:
    Concierge -> Scout -> (Signal + Hunter) for top N events.
    """
    try:
        # Hard safety clamps to prevent accidental runaway spend.
        max_events = min(max(req.max_events, 0), 20)   # Tavily calls can be expensive too
        max_hunter = min(max(req.max_hunter, 0), 10)  # each triggers 1 Claude + 1 Firecrawl
        try:
            plan = generate_search_schema(req.user_query)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"concierge_failed: {e}")

        scout = SignalScout()
        try:
            events = await scout.run(plan.search_queries)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"scout_failed: {e}")
        events = events[:max_events]

        try:
            engine = SignalEngine()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"signal_init_failed: {e}")
        try:
            hunter = UniversalHunter()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"hunter_init_failed: {e}")

        inferences: List[SignalInference] = []
        extracted: List[HunterExtractResponse] = []

        for ev in events[:max_hunter]:
            # Signal uses the raw event snippet as text input
            try:
                inf = await engine.process_raw_data(plan.industry, ev.snippet, ev.event_date)
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"signal_failed: {e}")
            inferences.append(inf)

            try:
                ext = await hunter.run(ev.event_url)
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"hunter_failed: {e}")
            extracted.append(HunterExtractResponse(**ext))

        return PipelineRunResponse(plan=plan, events=events, inferences=inferences, extracted=extracted)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve built frontend (single Railway service / single PORT).
# IMPORTANT: mount this last so /health and /api/* routes win.
_repo_root = Path(__file__).resolve().parents[2]
_frontend_dist = _repo_root / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
