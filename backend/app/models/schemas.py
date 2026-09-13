from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Criterion(BaseModel):
    name: str
    unit: str | None = None
    aliases: list[str] = Field(default_factory=list)
    norm_min: float | None = None
    norm_max: float | None = None
    yellow_min: float | None = None
    yellow_max: float | None = None
    critical: bool = True


class CriteriaSet(BaseModel):
    product_type: str = "coffee"
    source_filename: str = ""
    criteria: list[Criterion] = Field(default_factory=list)
    system_prompt_text: str = ""


class ProtocolRow(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    raw_value: str | None = None


class ParameterResult(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    allowed: str
    status: Verdict
    criterion_name: str | None = None


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    report_text: str
    parameters: list[ParameterResult]
    unmapped_params: list[str] = Field(default_factory=list)
    product_type: str = "coffee"


class HealthResponse(BaseModel):
    status: str
    gigachat: bool
    database: str
