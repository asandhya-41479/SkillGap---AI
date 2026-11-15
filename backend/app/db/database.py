from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# pool_pre_ping: test each pooled connection before use, so a connection the
# hosted database closed while idle (Neon does this) is replaced, not reused.
# pool_recycle: replace connections older than 5 minutes for the same reason.
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()