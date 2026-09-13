from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.graph.analyze import run_analyze
from app.graph.ingest import ingest_table
from app.llm import gigachat_client
from app.models.schemas import AnalyzeResponse, CriteriaSet, HealthResponse, Verdict
from app.services.criteria_store import database_status, load_criteria, save_criteria
from app.services.excel import parse_protocol

app = FastAPI(title="Solyaris Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        gigachat=gigachat_client.is_configured(),
        database=database_status(),
    )


@app.get("/api/criteria", response_model=CriteriaSet)
def get_criteria() -> CriteriaSet:
    criteria = load_criteria()
    if criteria is None:
        raise HTTPException(status_code=404, detail="CORE criteria are not loaded yet")
    return criteria


@app.post("/api/criteria/ingest", response_model=CriteriaSet)
async def ingest_criteria(file: UploadFile = File(...)) -> CriteriaSet:
    content = await file.read()
    try:
        criteria = ingest_table(content, file.filename or "norms.xlsx")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return save_criteria(criteria)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)) -> AnalyzeResponse:
    criteria = load_criteria()
    if criteria is None:
        raise HTTPException(status_code=409, detail="Upload CORE/GOST file first")
    content = await file.read()
    try:
        rows = parse_protocol(content, file.filename or "protocol.xlsx")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="Protocol file has no rows")
    state = run_analyze(rows, criteria)
    return AnalyzeResponse(
        verdict=Verdict(state["verdict"]),
        report_text=state.get("report_text", ""),
        parameters=state.get("parameters", []),
        unmapped_params=state.get("unmapped_params", []),
        product_type=criteria.product_type,
    )
