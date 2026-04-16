from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./air.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)           # 방송명
    channel = Column(String, nullable=True)          # 채널명
    video_path = Column(String, nullable=False)      # 업로드된 영상 경로
    status = Column(String, default="pending")       # pending / processing / done / failed
    products = Column(JSON, default=[])              # 인식된 상품 목록
    webapp_path = Column(String, nullable=True)      # 생성된 웹앱 경로
    webapp_url = Column(String, nullable=True)       # 웹앱 접근 URL
    popup_enabled = Column(String, default="on")     # on / off
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
