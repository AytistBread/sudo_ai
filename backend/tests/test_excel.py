from io import BytesIO

import pandas as pd

from app.services.excel import parse_protocol


def test_parse_protocol_reads_all_excel_sheets() -> None:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"Параметр": ["Влажность"], "Значение": [11.0]}).to_excel(
            writer, sheet_name="Страница 1", index=False
        )
        pd.DataFrame({"Параметр": ["Дефекты зёрен"], "Значение": [2.0]}).to_excel(
            writer, sheet_name="Страница 2", index=False
        )

    rows = parse_protocol(output.getvalue(), "protocol.xlsx")

    assert [row.name for row in rows] == ["Влажность", "Дефекты зёрен"]