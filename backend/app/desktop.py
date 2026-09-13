from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from app.graph.analyze import run_analyze
from app.graph.ingest import ingest_table
from app.models.schemas import Verdict
from app.services.criteria_store import load_criteria, save_criteria
from app.services.excel import parse_protocol

BG = "#2B2825"
SURFACE = "#37332F"
SURFACE_2 = "#433E39"
LINE = "#534E48"
TEXT = "#F0EBE4"
MUTED = "#A8A29A"
PAPER = "#D8D2C6"
SUCCESS = "#7A9E82"
WARN = "#D0B56A"
DANGER = "#D07A6C"

VERDICT_LABEL = {
    Verdict.GREEN: "Годна",
    Verdict.YELLOW: "Внимание",
    Verdict.RED: "Брак",
}
VERDICT_COLOR = {
    Verdict.GREEN: SUCCESS,
    Verdict.YELLOW: WARN,
    Verdict.RED: DANGER,
}


def _card(title: str, body: list[ft.Control]) -> ft.Container:
    return ft.Container(
        bgcolor=SURFACE,
        border=ft.Border.all(1, LINE),
        border_radius=6,
        padding=20,
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(title, size=12, color=MUTED),
                *body,
            ],
        ),
    )


def _status_chip(text: str, color: str) -> ft.Container:
    return ft.Container(
        bgcolor=SURFACE_2,
        border=ft.Border.all(1, color),
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        content=ft.Text(text, size=12, color=color),
    )


def _criteria_summary(criteria) -> str:
    lines = [f"Файл: {criteria.source_filename or 'без имени'}", f"Критериев: {len(criteria.criteria)}"]
    for item in criteria.criteria:
        minimum = "нет" if item.norm_min is None else str(item.norm_min)
        maximum = "нет" if item.norm_max is None else str(item.norm_max)
        unit = f" {item.unit}" if item.unit else ""
        lines.append(f"• {item.name}: от {minimum} до {maximum}{unit}")
    return "\n".join(lines)


async def main(page: ft.Page) -> None:
    page.title = "Солярис — выбраковка"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 32
    page.scroll = ft.ScrollMode.AUTO
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=PAPER,
            on_primary="#2B2825",
            surface=SURFACE,
            on_surface=TEXT,
            error=DANGER,
            outline=LINE,
        ),
        font_family="Segoe UI",
    )
    page.window.width = 1140
    page.window.height = 800
    page.window.min_width = 960
    page.window.min_height = 680
    page.window.bgcolor = BG

    picker = ft.FilePicker()
    state: dict = {"norms": None, "protocol": None}

    norms_name = ft.Text("Файл не выбран", color=MUTED, size=14)
    protocol_name = ft.Text("Файл не выбран", color=MUTED, size=14)
    core_label = ft.Text("", size=12, color=MUTED)
    core_preview = ft.Text("Критерии ещё не загружены", size=12, color=MUTED)
    status = ft.Text("Готово к загрузке файлов", size=12, color=MUTED)
    verdict_title = ft.Text("Ожидание проверки", size=32, font_family="Georgia", color=TEXT)
    lamp = ft.Container(width=14, height=14, border_radius=7, bgcolor=MUTED)
    report = ft.Text("Загрузите нормативы, затем протокол испытаний.", size=14, color=TEXT)
    table = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    current = load_criteria(local_only=True)
    if current is not None:
        core_label.value = f"CORE загружен · {len(current.criteria)} критериев"
        core_label.color = SUCCESS
        core_preview.value = _criteria_summary(current)

    async def pick(kind: str) -> None:
        files = await picker.pick_files(
            dialog_title="Нормативы ГОСТ / ТУ" if kind == "norms" else "Протокол испытаний",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx", "xls", "csv"],
        )
        if not files:
            return
        path = Path(files[0].path or "")
        if kind == "norms":
            state["norms"] = path
            norms_name.value = path.name
            norms_name.color = TEXT
        else:
            state["protocol"] = path
            protocol_name.value = path.name
            protocol_name.color = TEXT
        page.update()

    async def pick_norms(_e=None) -> None:
        await pick("norms")

    async def pick_protocol(_e=None) -> None:
        await pick("protocol")

    async def ingest(_e=None) -> None:
        path: Path | None = state["norms"]
        if path is None:
            status.value = "Сначала выберите файл нормативов"
            status.color = DANGER
            page.update()
            return
        status.value = "Сохраняю CORE…"
        status.color = MUTED
        page.update()
        try:
            criteria = await asyncio.to_thread(ingest_table, path.read_bytes(), path.name)
            await asyncio.to_thread(save_criteria, criteria, True)
            core_label.value = f"CORE сохранён · {len(criteria.criteria)} критериев"
            core_label.color = SUCCESS
            core_preview.value = _criteria_summary(criteria)
            status.value = "CORE готов"
            status.color = MUTED
        except Exception as exc:
            status.value = str(exc)
            status.color = DANGER
        page.update()

    async def analyze(_e=None) -> None:
        path: Path | None = state["protocol"]
        if path is None:
            status.value = "Сначала выберите протокол"
            status.color = DANGER
            page.update()
            return
        status.value = "Сверяю протокол с CORE…"
        status.color = MUTED
        page.update()
        try:
            criteria = await asyncio.to_thread(load_criteria, True)
            if criteria is None:
                raise ValueError("Сначала сохраните CORE из файла нормативов")

            def work():
                rows = parse_protocol(path.read_bytes(), path.name)
                if not rows:
                    raise ValueError("В протоколе нет строк")
                return run_analyze(rows, criteria)

            result = await asyncio.to_thread(work)
            verdict = Verdict(result["verdict"])
            color = VERDICT_COLOR[verdict]
            lamp.bgcolor = color
            verdict_title.value = VERDICT_LABEL[verdict]
            verdict_title.color = color
            text = result.get("report_text") or ""
            unmapped = result.get("unmapped_params") or []
            if unmapped:
                text = f"{text}\n\nНе сопоставлено: {', '.join(unmapped)}"
            report.value = text
            table.controls.clear()
            for row in result.get("parameters", []):
                tone = VERDICT_COLOR[row.status]
                value = "—" if row.value is None else f"{row.value} {row.unit or ''}".strip()
                table.controls.append(
                    ft.Container(
                        bgcolor=SURFACE_2,
                        border=ft.Border.only(left=ft.BorderSide(3, tone)),
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        content=ft.Row(
                            controls=[
                                ft.Text(row.name, expand=3, size=13),
                                ft.Text(value, expand=2, size=13, color=MUTED),
                                ft.Text(row.allowed, expand=3, size=13, color=MUTED),
                                _status_chip(VERDICT_LABEL[row.status], tone),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                )
            status.value = "Проверка завершена"
            status.color = MUTED
        except Exception as exc:
            status.value = str(exc)
            status.color = DANGER
            lamp.bgcolor = MUTED
            verdict_title.value = "Ошибка"
            verdict_title.color = DANGER
        page.update()

    page.add(
        ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("ООО СОЛЯРИС  ·  контроль качества", size=12, color=MUTED),
                        ft.Text(
                            "Выбраковка сырья и готовой продукции",
                            size=28,
                            font_family="Georgia",
                            color=TEXT,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=16,
                    controls=[
                        _card(
                            "Нормативы ГОСТ / ТУ",
                            [
                                norms_name,
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.OutlinedButton(content="Выбрать файл", on_click=pick_norms),
                                        ft.OutlinedButton(content="Сохранить CORE", on_click=ingest),
                                    ],
                                ),
                                core_label,
                                ft.Container(
                                    bgcolor=SURFACE_2,
                                    border=ft.Border.all(1, LINE),
                                    border_radius=4,
                                    padding=12,
                                    content=core_preview,
                                ),
                            ],
                        ),
                        _card(
                            "Протокол лаборатории",
                            [
                                protocol_name,
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.OutlinedButton(content="Выбрать файл", on_click=pick_protocol),
                                        ft.Button(content="Проверить партию", on_click=analyze),
                                    ],
                                ),
                                ft.Text(
                                    "Вердикт фиксирует только факт. Причины — у комиссии.",
                                    size=12,
                                    color=MUTED,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor=SURFACE,
                    border=ft.Border.all(1, LINE),
                    border_radius=6,
                    padding=20,
                    content=ft.Row(
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            lamp,
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("РЕЗУЛЬТАТ ПАРТИИ", size=11, color=MUTED),
                                    verdict_title,
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Отчёт оператору", size=12, color=MUTED),
                        ft.Container(
                            bgcolor=SURFACE,
                            border=ft.Border.all(1, LINE),
                            border_radius=6,
                            padding=16,
                            content=report,
                        ),
                    ],
                ),
                ft.Text("Параметры", size=12, color=MUTED),
                ft.Container(expand=True, content=table),
                status,
            ],
        )
    )


def run() -> None:
    ft.run(main, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    run()
