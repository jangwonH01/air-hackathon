"""
AIR - AI Instant Retail
FastAPI 메인 서버
"""
import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from models import init_db, get_db, AnalysisJob
from tasks import analyze_video

UPLOAD_DIR = "./uploads"
GENERATED_APPS_DIR = os.getenv("GENERATED_APPS_DIR", "./generated_apps")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_APPS_DIR, exist_ok=True)

app = FastAPI(title="AIR - AI Instant Retail", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 생성된 웹앱 정적 파일 서빙
app.mount("/apps", StaticFiles(directory=GENERATED_APPS_DIR), name="apps")


@app.on_event("startup")
def startup():
    init_db()


# ── 관리자 API ──────────────────────────────────────────────

@app.post("/api/jobs")
async def create_job(
    title: str = Form(...),
    channel: str = Form(""),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """영상 업로드 및 분석 시작"""
    # 파일 저장
    ext = Path(video.filename).suffix
    save_path = os.path.join(UPLOAD_DIR, f"video_{title[:20]}{ext}")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # DB 저장
    job = AnalysisJob(title=title, channel=channel, video_path=save_path)
    db.add(job)
    db.commit()
    db.refresh(job)

    # 비동기 분석 시작
    analyze_video.delay(job.id, save_path, title, channel)

    return {"job_id": job.id, "status": "processing", "message": "분석을 시작했습니다."}


@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    """전체 작업 목록"""
    jobs = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).all()
    return [_job_to_dict(j) for j in jobs]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """작업 상태 및 결과 조회"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return _job_to_dict(job)


@app.patch("/api/jobs/{job_id}/popup")
def toggle_popup(job_id: int, enabled: bool, db: Session = Depends(get_db)):
    """팝업 노출 ON/OFF"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    job.popup_enabled = "on" if enabled else "off"
    db.commit()
    return {"popup_enabled": job.popup_enabled}


# ── TV 웹앱 API ─────────────────────────────────────────────

@app.get("/api/popup/latest")
def get_latest_popup(db: Session = Depends(get_db)):
    """셋탑 홈화면에 노출할 최신 팝업 정보"""
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.status == "done", AnalysisJob.popup_enabled == "on")
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )
    if not job:
        return {"popup": None}

    return {
        "popup": {
            "job_id": job.id,
            "title": job.title,
            "channel": job.channel,
            "product_count": len(job.products or []),
            "webapp_url": job.webapp_url,
        }
    }


# ── 헬스체크 ────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "AIR"}


def _job_to_dict(job: AnalysisJob) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "channel": job.channel,
        "status": job.status,
        "product_count": len(job.products or []),
        "products": job.products or [],
        "webapp_url": job.webapp_url,
        "popup_enabled": job.popup_enabled,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
