from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# SQLite needs check_same_thread=False for FastAPI concurrency
resolved_url = settings.resolved_database_url
engine = create_engine(
    resolved_url,
    connect_args={"check_same_thread": False} if "sqlite" in resolved_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
