# Solyaris Agent

Локальный прототип AI-агента для ООО «Солярис»: выбраковка сырья/готовой продукции по протоколу лаборатории и эталонным ГОСТам/ТУ.

Стек: Python-окно (Flet), Pandas, LangGraph, GigaChat SDK (`from gigachat import GigaChat`), FastAPI по желанию, Postgres/pgvector, Docker.

Агент не ищет причины брака и не предлагает решений — только светофор и перечень отклонений.

Проект лежит в `Documents/solyaris-agent` — это обычный VS Code/Cursor workspace, не Qt.

Нужен Python 3.12 (`py -3.12`). На 3.14 колёс у Pandas нет.

## Запуск локально

Оболочка — десктопное окно, браузер не нужен.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example ..\.env
python -m app.desktop
```

В VS Code: конфигурация **Solyaris Desktop**.

### Docker

```powershell
copy .env.example .env
docker compose up --build
```

UI: http://localhost:8080 · API: http://localhost:8000

Ключ GigaChat (`GIGACHAT_CREDENTIALS`) нужен только для извлечения CORE из «кривого» Excel и текстового отчёта. Светофор считается кодом и работает без модели.
