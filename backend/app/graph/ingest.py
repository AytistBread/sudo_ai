import json
import re

import pandas as pd
from langgraph.graph import END, START, StateGraph

from app.graph.state import IngestState
from app.llm import gigachat_client
from app.models.schemas import CriteriaSet, Criterion
from app.services.excel import read_table

EXTRACT_SYSTEM = """Ты извлекаешь CORE-критерии сортировки кофе из таблицы нормативов.
Верни только JSON объекта:
{"product_type":"...","criteria":[{"name":"...","unit":"...","aliases":[],"norm_min":0,"norm_max":0,"yellow_min":null,"yellow_max":null,"critical":true}]}
Не добавляй причины брака и рекомендации. Числа должны быть числами, не строками."""


def _structured_from_frame(frame: pd.DataFrame, filename: str) -> CriteriaSet | None:
    columns = {_header(column): column for column in frame.columns}
    name_col = _find_column(
        columns,
        "name",
        "parameter",
        "param",
        "параметр",
        "показатель",
        "наименование",
        "наименование показателя",
    )
    if not name_col:
        return None

    unit_col = _find_column(columns, "unit", "ед", "единица", "единица измерения")
    min_col = _find_column(columns, "norm_min", "min", "мин", "минимум")
    max_col = _find_column(columns, "norm_max", "max", "макс", "максимум")
    norm_col = _find_column(columns, "норма", "норматив", "требования", "допуск")
    yellow_min_col = _find_column(columns, "yellow_min")
    yellow_max_col = _find_column(columns, "yellow_max")
    items: list[Criterion] = []
    for _, row in frame.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == "nan":
            continue
        parsed_min, parsed_max = _parse_norm(row.get(norm_col) if norm_col else None)
        explicit_min = _num(row.get(min_col) if min_col else None)
        explicit_max = _num(row.get(max_col) if max_col else None)
        items.append(
            Criterion(
                name=name,
                unit=None if not unit_col or pd.isna(row[unit_col]) else str(row[unit_col]),
            norm_min=explicit_min if explicit_min is not None else parsed_min,
            norm_max=explicit_max if explicit_max is not None else parsed_max,
                yellow_min=_num(row.get(yellow_min_col) if yellow_min_col else None),
                yellow_max=_num(row.get(yellow_max_col) if yellow_max_col else None),
            )
        )
    if not items:
        return None
    criteria = CriteriaSet(product_type="coffee", source_filename=filename, criteria=items)
    criteria.system_prompt_text = build_system_prompt(criteria)
    return criteria


def build_system_prompt(criteria: CriteriaSet) -> str:
    lines = [
        "Ты операторский ассистент выбраковки кофе.",
        "Сверяй только факты с CORE. Не ищи причины. Не предлагай решений.",
        f"Тип продукции: {criteria.product_type}.",
        "CORE-критерии:",
    ]
    for item in criteria.criteria:
        lines.append(
            f"- {item.name}: min={item.norm_min}, max={item.norm_max}, "
            f"yellow=[{item.yellow_min}, {item.yellow_max}], unit={item.unit}"
        )
    return "\n".join(lines)


def extract_criteria(state: IngestState) -> IngestState:
    preview = state.get("table_preview", "")
    filename = state.get("filename", "norms.xlsx")
    try:
        payload = json.loads(preview)
        frame = pd.DataFrame(payload)
    except Exception as exc:
        return {"error": f"cannot parse table preview: {exc}"}

    structured = _structured_from_frame(frame, filename)
    if structured is not None:
        return {"criteria": structured}

    if not gigachat_client.is_configured():
        return {"error": "Need structured columns (параметр/min/max) or GIGACHAT_CREDENTIALS"}

    raw = gigachat_client.chat(EXTRACT_SYSTEM, preview[:12000])
    data = json.loads(_extract_json(raw))
    criteria = CriteriaSet.model_validate({**data, "source_filename": filename})
    criteria.system_prompt_text = build_system_prompt(criteria)
    return {"criteria": criteria}


def build_ingest_graph():
    graph = StateGraph(IngestState)
    graph.add_node("extract_criteria", extract_criteria)
    graph.add_edge(START, "extract_criteria")
    graph.add_edge("extract_criteria", END)
    return graph.compile()


def ingest_table(content: bytes, filename: str) -> CriteriaSet:
    frame = read_table(content, filename)
    preview = frame.to_json(orient="records", force_ascii=False)
    result = build_ingest_graph().invoke({"filename": filename, "table_preview": preview})
    if result.get("error"):
        raise ValueError(result["error"])
    return result["criteria"]


def _num(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _header(value: object) -> str:
    return " ".join(str(value).casefold().replace("\n", " ").split())


def _find_column(columns: dict[str, object], *aliases: str) -> object | None:
    normalized = {_header(alias) for alias in aliases}
    for key, column in columns.items():
        if key in normalized:
            return column
    return None


def _parse_norm(value: object) -> tuple[float | None, float | None]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None
    text = str(value).casefold().replace(",", ".").strip()
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None, None
    if len(numbers) >= 2 and (" до " in text or "-" in text or "–" in text):
        return numbers[0], numbers[1]
    if "не более" in text or "не выше" in text or "до " in text:
        return None, numbers[-1]
    if "не менее" in text or "не ниже" in text or "от " in text:
        return numbers[0], None
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return None, numbers[0]


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("GigaChat did not return JSON")
    return text[start : end + 1]
