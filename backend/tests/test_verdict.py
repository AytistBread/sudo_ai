from app.models.schemas import CriteriaSet, Criterion, ProtocolRow, Verdict
from app.services.verdict import analyze_protocol, compare_value, overall_verdict


def _humidity() -> Criterion:
    return Criterion(
        name="Влажность",
        unit="%",
        norm_min=9.0,
        norm_max=12.5,
        yellow_min=9.5,
        yellow_max=12.0,
    )


def test_green_inside_yellow_band() -> None:
    assert compare_value(11.0, _humidity()) == Verdict.GREEN


def test_yellow_near_boundary() -> None:
    assert compare_value(12.3, _humidity()) == Verdict.YELLOW


def test_red_outside_norm() -> None:
    assert compare_value(14.8, _humidity()) == Verdict.RED


def test_overall_red_wins() -> None:
    criteria = CriteriaSet(criteria=[_humidity(), Criterion(name="Дефекты зёрен", norm_min=0, norm_max=5)])
    rows = [
        ProtocolRow(name="Влажность", value=11.0),
        ProtocolRow(name="Дефекты зёрен", value=8.5),
    ]
    results, unmapped = analyze_protocol(rows, criteria)
    assert unmapped == []
    assert overall_verdict(results) == Verdict.RED
