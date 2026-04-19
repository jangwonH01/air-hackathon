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
from tasks import analyze_video, record_live

UPLOAD_DIR = "./uploads"
GENERATED_APPS_DIR = os.getenv("GENERATED_APPS_DIR", "./generated_apps")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AIR - AI Instant Retail", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STILLS_DIR = "./stills"
os.makedirs(STILLS_DIR, exist_ok=True)
os.makedirs(GENERATED_APPS_DIR, exist_ok=True)

# 생성된 웹앱 정적 파일 서빙
app.mount("/apps", StaticFiles(directory=GENERATED_APPS_DIR), name="apps")
app.mount("/stills", StaticFiles(directory=STILLS_DIR), name="stills")


@app.on_event("startup")
def startup():
    init_db()


# ── 관리자 API ──────────────────────────────────────────────

@app.post("/api/jobs")
async def create_job(
    title: str = Form(...),
    channel: str = Form(""),
    video: UploadFile = File(None),
    url: str = Form(""),
    is_live: str = Form("no"),
    db: Session = Depends(get_db),
):
    """영상 업로드, URL, 또는 라이브 방송 분석 시작"""
    if url and is_live == "yes":
        # 라이브 녹화 모드
        job = AnalysisJob(title=title, channel=channel, video_path="", source_url=url, is_live="yes", status="waiting")
        db.add(job)
        db.commit()
        db.refresh(job)
        record_live.delay(job.id, url, title, channel)
        return {"job_id": job.id, "status": "waiting", "message": "라이브 방송 모니터링을 시작했습니다."}
    elif url:
        job = AnalysisJob(title=title, channel=channel, video_path="", source_url=url, status="pending")
        db.add(job)
        db.commit()
        db.refresh(job)
        analyze_video.delay(job.id, "", title, channel, url=url)
    elif video:
        ext = Path(video.filename).suffix
        # 먼저 job을 만들어 id를 확보
        job = AnalysisJob(title=title, channel=channel, video_path="")
        db.add(job)
        db.commit()
        db.refresh(job)
        save_path = os.path.join(UPLOAD_DIR, f"video_{job.id}{ext}")
        with open(save_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
        job.video_path = save_path
        db.commit()
        analyze_video.delay(job.id, save_path, title, channel)
    else:
        raise HTTPException(status_code=400, detail="영상 파일 또는 URL을 입력해주세요.")

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


@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: int, db: Session = Depends(get_db)):
    """실패/대기 작업 재시도"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    job.status = "pending"
    db.commit()
    analyze_video.delay(job.id, job.video_path or "", job.title, job.channel or "", url=job.source_url or "")
    return {"job_id": job.id, "status": "processing", "message": "재시도를 시작했습니다."}


@app.patch("/api/jobs/{job_id}")
def update_job(job_id: int, title: str = None, channel: str = None, db: Session = Depends(get_db)):
    """작업 제목/채널 수정"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    if title is not None:
        job.title = title
    if channel is not None:
        job.channel = channel
    db.commit()
    return _job_to_dict(job)


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """작업 삭제"""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    db.delete(job)
    db.commit()
    return {"message": "삭제됐습니다."}


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
        "is_live": job.is_live or "no",
        "source_url": job.source_url or "",
        "product_count": len(job.products or []),
        "products": job.products or [],
        "webapp_url": job.webapp_url,
        "popup_enabled": job.popup_enabled,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
