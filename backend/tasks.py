"""
Celery 비동기 작업 - 영상 분석 파이프라인
"""
import os
import sys
import asyncio
from celery import Celery
from dotenv import load_dotenv

# 백엔드 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

celery = Celery("air", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))


@celery.task(bind=True)
def analyze_video(self, job_id: int, video_path: str, title: str, channel: str, url: str = ""):
    """
    전체 파이프라인 실행:
    영상 → 프레임 추출 → AI 제품 인식 → 쇼핑 매칭 → 웹앱 생성
    """
    from models import SessionLocal, AnalysisJob
    from ai.extractor import extract_frames
    from ai.vision import recognize_products_from_frames
    from ai.shopping import match_products
    from ai.generator import generate_shopping_webapp, save_webapp

    db = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    try:
        # 1. 상태 업데이트: 처리 중
        job.status = "processing"
        db.commit()

        # 2. URL이면 먼저 다운로드
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        if url and not video_path:
            import subprocess
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

        # 3. 프레임 추출
        frames_dir = os.path.join(BASE_DIR, "frames", f"job_{job_id}")
        frames = extract_frames(video_path, frames_dir, fps=0.5)
        print(f"[Pipeline] 프레임 추출 완료: {len(frames)}개")

        # 3. AI 제품 인식
        raw_products = recognize_products_from_frames(frames, title=title, channel=channel)
        print(f"[Pipeline] 인식된 상품: {len(raw_products)}개")

        # 4. 네이버 쇼핑 매칭
        matched = asyncio.run(match_products(raw_products))
        print(f"[Pipeline] 매칭된 상품: {len(matched)}개")

        # 5. 웹앱 자동 생성
        html = generate_shopping_webapp(title, channel, matched)
        apps_dir = os.getenv("GENERATED_APPS_DIR", "./generated_apps")
        webapp_path = save_webapp(job_id, html, apps_dir)
        webapp_url = f"/apps/shop_{job_id}.html"
        print(f"[Pipeline] 웹앱 생성 완료: {webapp_path}")

        # 6. 완료 저장
        job.status = "done"
        job.products = matched
        job.webapp_path = webapp_path
        job.webapp_url = webapp_url
        db.commit()

    except Exception as e:
        job.status = "failed"
        db.commit()
        print(f"[Pipeline] 오류: {e}")
        raise

    finally:
        db.close()
