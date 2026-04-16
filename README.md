# AIR - AI Instant Retail

> 방송이 끝나는 순간, 쇼핑이 시작된다.

## 프로젝트 구조

```
air-hackathon/
├── index.html              # 웹 제안서
├── backend/                # FastAPI 서버
│   ├── main.py             # API 엔드포인트
│   ├── models.py           # DB 모델
│   ├── tasks.py            # Celery 비동기 작업
│   ├── ai/
│   │   ├── extractor.py    # ffmpeg 프레임 추출
│   │   ├── vision.py       # Claude Vision 제품 인식
│   │   ├── shopping.py     # 네이버 쇼핑 API 매칭
│   │   └── generator.py    # 웹앱 자동 생성
│   └── requirements.txt
└── frontend/
    ├── tv/
    │   └── popup.html      # TV 팝업 UI (Vanilla JS)
    └── admin/              # 관리자 대시보드 (React)
```

## 실행 방법

### 1. 환경 설정
```bash
cd backend
cp .env.example .env
# .env에 API 키 입력
```

### 2. 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Celery Worker 실행 (새 터미널)
```bash
cd backend
celery -A tasks worker --loglevel=info
```

### 4. Redis 실행 (새 터미널)
```bash
redis-server
```

### 5. 관리자 대시보드 실행 (새 터미널)
```bash
cd frontend/admin
npm install
npm run dev
```

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /api/jobs | 영상 업로드 및 분석 시작 |
| GET | /api/jobs | 전체 작업 목록 |
| GET | /api/jobs/{id} | 작업 상태 조회 |
| PATCH | /api/jobs/{id}/popup | 팝업 ON/OFF |
| GET | /api/popup/latest | 최신 팝업 정보 (TV용) |
