from langgraph.graph import END, START, StateGraph

from app.graph.state import AnalyzeState
from app.llm import gigachat_client
from app.llm.gigachat_client import GigaChatNotConfigured
from app.models.schemas import CriteriaSet, ProtocolRow, Verdict
from app.services.verdict import analyze_protocol, overall_verdict

REPORT_GUARD = (
    "Запрещено писать причины брака, рекомендации, переработку, списание "
    "и любые советы комиссии. Только факт и допуск."
)


def analyze_node(state: AnalyzeState) -> AnalyzeState:
    criteria: CriteriaSet = state["criteria"]
    rows: list[ProtocolRow] = state["rows"]
    parameters, unmapped = analyze_protocol(rows, criteria)
    verdict = overall_verdict(parameters)
    return {
        "parameters": parameters,
        "unmapped_params": unmapped,
        "verdict": verdict.value,
        "system_prompt": criteria.system_prompt_text or "",
    }


def report_node(state: AnalyzeState) -> AnalyzeState:
    verdict = Verdict(state["verdict"])
    parameters = state.get("parameters", [])
    deviations = [item for item in parameters if item.status != Verdict.GREEN]
    fallback = _template_report(verdict, deviations)
    system = state.get("system_prompt") or "Ты пишешь короткий отчёт оператору по выбраковке кофе."
    user = (
        f"{REPORT_GUARD}\nВердикт: {verdict.value}.\n"
        f"Отклонения: {[item.model_dump() for item in deviations]}\n"
        "Напиши 5-8 предложений на русском: перечень выходов за норму, факт и допуск."
    )
    try:
        text = gigachat_client.chat(system + "\n" + REPORT_GUARD, user)
        if _looks_like_advice(text):
            text = fallback
    except GigaChatNotConfigured:
        text = fallback
    except Exception:
        text = fallback
    return {"report_text": text}


def build_analyze_graph():
    graph = StateGraph(AnalyzeState)
    graph.add_node("analyze", analyze_node)
    graph.add_node("report", report_node)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "report")
    graph.add_edge("report", END)
    return graph.compile()


def run_analyze(rows: list[ProtocolRow], criteria: CriteriaSet) -> AnalyzeState:
    return build_analyze_graph().invoke({"rows": rows, "criteria": criteria})


def _template_report(verdict: Verdict, deviations: list) -> str:
    if verdict == Verdict.GREEN:
        return "Все сопоставленные параметры в норме. Продукция годна по загруженным критериям."
    lines = [f"Вердикт: {verdict.value}. Параметры вне зелёной зоны:"]
    for item in deviations:
        lines.append(f"- {item.name}: факт {item.value} {item.unit or ''}, допуск {item.allowed}")
    lines.append("Причины и решения агент не анализирует — это зона комиссии.")
    return "\n".join(lines)


def _looks_like_advice(text: str) -> bool:
    banned = ("рекоменд", "переработ", "списат", "предлага", "причин")
    lowered = text.casefold()
    return any(word in lowered for word in banned)
