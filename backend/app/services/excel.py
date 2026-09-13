from io import BytesIO
from pathlib import Path

import pandas as pd

from app.models.schemas import ProtocolRow


def read_tables(content: bytes, filename: str) -> list[pd.DataFrame]:
    suffix = Path(filename).suffix.lower()
    buffer = BytesIO(content)
    if suffix in {".xlsx", ".xls"}:
        frames = list(pd.read_excel(buffer, sheet_name=None).values())
    elif suffix == ".csv":
        frames = [pd.read_csv(buffer)]
    else:
        raise ValueError(f"Unsupported file type: {suffix or filename}")
    result = []
    for frame in frames:
        frame.columns = [str(column).strip() for column in frame.columns]
        result.append(frame.dropna(how="all"))
    return result


def read_table(content: bytes, filename: str) -> pd.DataFrame:
    """Return all pages as one table for existing ingestion callers."""
    frames = read_tables(content, filename)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def protocol_from_wide_table(frame: pd.DataFrame) -> list[ProtocolRow]:
    """One-row protocol: columns are parameter names."""
    if frame.empty:
        return []
    row = frame.iloc[0]
    items: list[ProtocolRow] = []
    for name, value in row.items():
        raw = None if pd.isna(value) else str(value)
        numeric = _to_float(value)
        items.append(ProtocolRow(name=str(name), value=numeric, raw_value=raw))
    return items


def protocol_from_long_table(frame: pd.DataFrame) -> list[ProtocolRow] | None:
    """Long format: parameter / value [/ unit] columns."""
    columns = {column.lower(): column for column in frame.columns}
    name_col = _first(columns, ("parameter", "param", "показатель", "параметр", "name"))
    value_col = _first(columns, ("value", "значение", "факт", "result"))
    unit_col = _first(columns, ("unit", "единица", "ед"))
    if not name_col or not value_col:
        return None
    items: list[ProtocolRow] = []
    for _, row in frame.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == "nan":
            continue
        value = row[value_col]
        unit = None if not unit_col or pd.isna(row[unit_col]) else str(row[unit_col])
        items.append(
            ProtocolRow(
                name=name,
                value=_to_float(value),
                unit=unit,
                raw_value=None if pd.isna(value) else str(value),
            )
        )
    return items


def parse_protocol(content: bytes, filename: str) -> list[ProtocolRow]:
    frames = read_tables(content, filename)
    if not frames:
        return []
    frame = pd.concat(frames, ignore_index=True)
    long_rows = protocol_from_long_table(frame)
    if long_rows:
        return long_rows
    return protocol_from_wide_table(frame)


def _to_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _first(columns: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        if alias in columns:
            return columns[alias]
    return None
