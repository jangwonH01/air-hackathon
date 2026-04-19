"""
Celery 비동기 작업 - 영상 분석 파이프라인
"""
import os
import sys
import asyncio
import subprocess
from celery import Celery
from dotenv import load_dotenv

# 백엔드 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

celery = Celery("air", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_pipeline(job, db, video_path: str, title: str, channel: str):
    """프레임 추출 → 상품 인식 → 쇼핑 매칭 → 웹앱 생성 공통 파이프라인"""
    from ai.extractor import extract_frames
    from ai.vision import recognize_products_from_frames
    from ai.shopping import match_products
    from ai.generator import generate_shopping_webapp, save_webapp

    job.status = "processing"
    db.commit()

    frames_dir = os.path.join(BASE_DIR, "frames", f"job_{job.id}")
    frames = extract_frames(video_path, frames_dir, fps=0.5)
    print(f"[Pipeline] 프레임 추출 완료: {len(frames)}개")

    stills_dir = os.path.join(BASE_DIR, "stills", f"job_{job.id}")
    raw_products = recognize_products_from_frames(frames, title=title, channel=channel, frames_serve_dir=stills_dir)
    print(f"[Pipeline] 인식된 상품: {len(raw_products)}개")

    matched = asyncio.run(match_products(raw_products))
    print(f"[Pipeline] 매칭된 상품: {len(matched)}개")

    apps_dir = os.getenv("GENERATED_APPS_DIR", os.path.join(BASE_DIR, "generated_apps"))

    # 상품이 2개 미만이면 쇼핑 웹앱 생성 불가 처리
    MIN_PRODUCTS = 2
    if len(matched) < MIN_PRODUCTS:
        print(f"[Pipeline] 상품 부족 ({len(matched)}개) → 쇼핑 웹앱 생성 건너뜀")
        job.status = "no_products"
        job.products = matched
        job.popup_enabled = "off"
        db.commit()
        return

    html = generate_shopping_webapp(title, channel, matched)
    webapp_path = save_webapp(job.id, html, apps_dir)
    webapp_url = f"/apps/shop_{job.id}.html"
    print(f"[Pipeline] 웹앱 생성 완료: {webapp_path}")

    job.status = "done"
    job.products = matched
    job.webapp_path = webapp_path
    job.webapp_url = webapp_url
    job.popup_enabled = "on"
    db.commit()


@celery.task(bind=True)
def analyze_video(self, job_id: int, video_path: str, title: str, channel: str, url: str = ""):
    """일반 영상 분석 파이프라인"""
    from models import SessionLocal, AnalysisJob

    db = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    try:
        job.status = "processing"
        db.commit()

        # URL이면 먼저 다운로드
        if url and not video_path:
            uploads_dir = os.path.join(BASE_DIR, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            video_path = os.path.join(uploads_dir, f"video_{job_id}.mp4")
            result = subprocess.run(
                ["yt-dlp", "-f", "mp4/best[height<=720]", "-o", video_path, url],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"다운로드 실패: {result.stderr}")
            job.video_path = video_path
            db.commit()

        _run_pipeline(job, db, video_path, title, channel)

    except Exception as e:
        job.status = "failed"
        db.commit()
        print(f"[Pipeline] 오류: {e}")
        raise
    finally:
        db.close()


@celery.task(bind=True)
def record_live(self, job_id: int, url: str, title: str, channel: str):
    """
    라이브 방송 녹화 + 종료 후 자동 분석
    yt-dlp가 라이브를 실시간 다운로드하다가 방송 종료 시 자동으로 분석 파이프라인 실행
    """
    from models import SessionLocal, AnalysisJob

    db = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    try:
        uploads_dir = os.path.join(BASE_DIR, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        video_path = os.path.join(uploads_dir, f"video_{job_id}.mp4")

        # 1. 방송 대기 및 녹화 시작
        job.status = "waiting"
        db.commit()
        print(f"[Live] 방송 대기/녹화 시작: {url}")

        result = subprocess.run(
            [
                "yt-dlp",
                "--wait-for-video", "10",      # 방송 시작 대기 (10초 간격 폴링)
                "--live-from-start",            # 방송 시작부터 녹화
                "-f", "mp4/best[height<=720]",
                "-o", video_path,
                url,
            ],
            capture_output=True, text=True
        )

        # 방송 시작되면 recording 상태로
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if result.returncode != 0:
            raise RuntimeError(f"라이브 녹화 실패: {result.stderr}")

        print(f"[Live] 방송 종료 감지 - 분석 시작")
        job.video_path = video_path
        job.status = "recording"
        db.commit()

        # 2. 방송 종료 후 자동 분석
        _run_pipeline(job, db, video_path, title, channel)
        print(f"[Live] 완료! 팝업 자동 활성화")

    except Exception as e:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        job.status = "failed"
        db.commit()
        print(f"[Live] 오류: {e}")
        raise
    finally:
        db.close()
