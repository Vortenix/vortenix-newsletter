from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
class Base(DeclarativeBase): pass
def engine(url="sqlite:///data/vortenix.db"):
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True,exist_ok=True)
    return create_engine(url)
def session_factory(url="sqlite:///data/vortenix.db"):
    return sessionmaker(engine(url),expire_on_commit=False)
def init_db(url="sqlite:///data/vortenix.db"):
    from . import orm_models  # noqa: F401
    Base.metadata.create_all(engine(url))
