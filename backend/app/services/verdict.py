from app.models.schemas import (
    CriteriaSet,
    Criterion,
    ParameterResult,
    ProtocolRow,
    Verdict,
)


def allowed_label(criterion: Criterion) -> str:
    parts: list[str] = []
    if criterion.norm_min is not None:
        parts.append(f">= {criterion.norm_min}")
    if criterion.norm_max is not None:
        parts.append(f"<= {criterion.norm_max}")
    if criterion.unit:
        parts.append(criterion.unit)
    return " ".join(parts) if parts else "—"


def compare_value(value: float, criterion: Criterion) -> Verdict:
    if _outside_norm(value, criterion):
        return Verdict.RED
    if _near_boundary(value, criterion):
        return Verdict.YELLOW
    return Verdict.GREEN


def analyze_protocol(rows: list[ProtocolRow], criteria: CriteriaSet) -> tuple[list[ParameterResult], list[str]]:
    results: list[ParameterResult] = []
    unmapped: list[str] = []
    used: set[str] = set()

    for row in rows:
        criterion = match_criterion(row.name, criteria, used)
        if criterion is None:
            unmapped.append(row.name)
            continue
        used.add(criterion.name)
        if row.value is None:
            results.append(
                ParameterResult(
                    name=row.name,
                    value=None,
                    unit=row.unit or criterion.unit,
                    allowed=allowed_label(criterion),
                    status=Verdict.YELLOW,
                    criterion_name=criterion.name,
                )
            )
            continue
        results.append(
            ParameterResult(
                name=row.name,
                value=row.value,
                unit=row.unit or criterion.unit,
                allowed=allowed_label(criterion),
                status=compare_value(row.value, criterion),
                criterion_name=criterion.name,
            )
        )
    return results, unmapped


def overall_verdict(results: list[ParameterResult]) -> Verdict:
    if any(item.status == Verdict.RED for item in results):
        return Verdict.RED
    if any(item.status == Verdict.YELLOW for item in results):
        return Verdict.YELLOW
    return Verdict.GREEN


def match_criterion(name: str, criteria: CriteriaSet, used: set[str]) -> Criterion | None:
    needle = _norm(name)
    for criterion in criteria.criteria:
        if criterion.name in used:
            continue
        aliases = [_norm(criterion.name), *(_norm(alias) for alias in criterion.aliases)]
        if needle in aliases:
            return criterion
    return None


def _outside_norm(value: float, criterion: Criterion) -> bool:
    if criterion.norm_min is not None and value < criterion.norm_min:
        return True
    if criterion.norm_max is not None and value > criterion.norm_max:
        return True
    return False


def _near_boundary(value: float, criterion: Criterion) -> bool:
    if criterion.yellow_min is not None and value < criterion.yellow_min:
        return True
    if criterion.yellow_max is not None and value > criterion.yellow_max:
        return True
    if criterion.yellow_min is not None or criterion.yellow_max is not None:
        return False
    if criterion.norm_min is None or criterion.norm_max is None:
        return False
    width = criterion.norm_max - criterion.norm_min
    if width <= 0:
        return False
    margin = width * 0.1
    return value <= criterion.norm_min + margin or value >= criterion.norm_max - margin


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())
