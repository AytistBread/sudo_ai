from typing import TypedDict

from app.models.schemas import CriteriaSet, ParameterResult, ProtocolRow


class IngestState(TypedDict, total=False):
    filename: str
    table_preview: str
    criteria: CriteriaSet
    error: str


class AnalyzeState(TypedDict, total=False):
    filename: str
    rows: list[ProtocolRow]
    criteria: CriteriaSet
    parameters: list[ParameterResult]
    unmapped_params: list[str]
    verdict: str
    report_text: str
    system_prompt: str
