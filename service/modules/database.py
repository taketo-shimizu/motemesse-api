from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/motemesse")

# テスト用フラグ
MOCK_DB = os.getenv("MOCK_DB", "false").lower() == "true"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    if MOCK_DB:
        # モックDB（実際には何も返さない）
        yield None
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()