from pathlib import Path

from sqlalchemy import JSON, Column, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings
from app.models.schemas import CriteriaSet

DATA_PATH = Path(settings.data_dir) / "core_criteria.json"


class Base(DeclarativeBase):
    pass


class CriteriaSetRow(Base):
    __tablename__ = "criteria_sets"

    id = Column(Integer, primary_key=True)
    product_type = Column(String(255), nullable=False, default="coffee")
    source_filename = Column(String(512), nullable=False, default="")
    payload = Column(JSON, nullable=False)
    system_prompt_text = Column(Text, nullable=False, default="")


_engine = None
_session_factory = None


def _engine_ready() -> bool:
    global _engine, _session_factory
    if _engine is not None:
        return True
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        Base.metadata.create_all(engine)
        _engine = engine
        _session_factory = sessionmaker(bind=engine)
        return True
    except Exception:
        _engine = None
        _session_factory = None
        return False


def database_status() -> str:
    return "up" if _engine_ready() else "file-fallback"


def save_criteria(criteria: CriteriaSet, local_only: bool = False) -> CriteriaSet:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(criteria.model_dump_json(indent=2), encoding="utf-8")
    if local_only or not _engine_ready() or _session_factory is None:
        return criteria
    with _session_factory() as session:
        session.query(CriteriaSetRow).delete()
        session.add(
            CriteriaSetRow(
                product_type=criteria.product_type,
                source_filename=criteria.source_filename,
                payload=criteria.model_dump(),
                system_prompt_text=criteria.system_prompt_text,
            )
        )
        session.commit()
    return criteria


def load_criteria(local_only: bool = False) -> CriteriaSet | None:
    if local_only:
        if DATA_PATH.exists():
            return CriteriaSet.model_validate_json(DATA_PATH.read_text(encoding="utf-8"))
        return None
    if _engine_ready() and _session_factory is not None:
        with _session_factory() as session:
            row = session.query(CriteriaSetRow).order_by(CriteriaSetRow.id.desc()).first()
            if row is not None:
                return CriteriaSet.model_validate(row.payload)
    if DATA_PATH.exists():
        return CriteriaSet.model_validate_json(DATA_PATH.read_text(encoding="utf-8"))
    return None
