"""
Google Cloud Vision API로 방송 프레임에서 상품을 인식합니다.
"""
import base64
import os
import shutil
import httpx
from pathlib import Path

GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
VISION_URL = "https://vision.googleapis.com/v1/images:annotate"

# (영어 태그, 한국어 검색어, 카테고리)
PRODUCT_TAG_MAP = [
    # 의류
    ("dress",       "원피스",       "의류"),
    ("shirt",       "셔츠",         "의류"),
    ("blouse",      "블라우스",     "의류"),
    ("jacket",      "자켓",         "의류"),
    ("coat",        "코트",         "의류"),
    ("outerwear",   "아우터",       "의류"),
    ("windbreaker", "바람막이",     "의류"),
    ("fur clothing","퍼 코트",      "의류"),
    ("pants",       "슬랙스",       "의류"),
    ("jeans",       "청바지",       "의류"),
    ("skirt",       "스커트",       "의류"),
    ("sweater",     "니트 스웨터",  "의류"),
    ("hoodie",      "후드티",       "의류"),
    ("top",         "여성 상의",    "의류"),
    ("clothing",    "캐주얼 의류",  "의류"),
    # 신발
    ("sneaker",     "스니커즈",     "신발"),
    ("shoe",        "구두",         "신발"),
    ("boot",        "부츠",         "신발"),
    ("sandal",      "샌들",         "신발"),
    ("heel",        "힐",           "신발"),
    ("footwear",    "운동화",       "신발"),
    # 가방
    ("handbag",     "핸드백",       "가방"),
    ("backpack",    "백팩",         "가방"),
    ("purse",       "지갑",         "가방"),
    ("tote",        "토트백",       "가방"),
    ("clutch",      "클러치백",     "가방"),
    ("bag",         "숄더백",       "가방"),
    # 액세서리
    ("watch",       "손목시계",     "액세서리"),
    ("sunglasses",  "선글라스",     "액세서리"),
    ("necklace",    "목걸이",       "액세서리"),
    ("earring",     "귀걸이",       "액세서리"),
    ("hat",         "모자",         "액세서리"),
    ("cap",         "볼캡",         "액세서리"),
    ("scarf",       "스카프",       "액세서리"),
    ("belt",        "벨트",         "액세서리"),
    ("jewelry",     "주얼리",       "액세서리"),
    # 가전
    ("phone",       "스마트폰",     "가전"),
    ("laptop",      "노트북",       "가전"),
    ("tablet",      "태블릿",       "가전"),
    ("camera",      "카메라",       "가전"),
    ("headphone",   "헤드폰",       "가전"),
    ("speaker",     "블루투스 스피커", "가전"),
    ("television",  "TV",           "가전"),
    # 생활용품
    ("cosmetic",    "화장품",       "생활용품"),
    ("skincare",    "스킨케어",     "생활용품"),
    ("lipstick",    "립스틱",       "생활용품"),
    ("furniture",   "인테리어 소품","생활용품"),
    ("lamp",        "무드등",       "생활용품"),
    ("pillow",      "쿠션",         "생활용품"),
    # 음식/음료
    ("coffee cup",  "텀블러",       "생활용품"),  # coffee는 음식 아니라 텀블러로
    ("food",        "먹거리",       "음식"),
    ("beverage",    "음료",         "음식"),
    ("meal",        "음식",         "음식"),
]


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def recognize_products_from_frames(frame_paths: list[str], title: str = "", channel: str = "", frames_serve_dir: str = "") -> list[dict]:
    """여러 프레임에서 상품을 인식하고 중복 제거 후 반환합니다."""

    if not GOOGLE_VISION_API_KEY:
        print("[Vision] GOOGLE_VISION_API_KEY 없음 → 목업 데이터 사용")
        return _mock_products(title, channel)

    # 프레임별로 분석하되 각 프레임에서 카테고리당 1개씩만 추출
    frame_results = []  # [(frame_path, product), ...]
    sampled = frame_paths[::max(1, len(frame_paths) // 10)][:10]

    for frame_path in sampled:
        products = _analyze_frame(frame_path)
        for p in products:
            p["_frame_path"] = frame_path
        frame_results.extend(products)

    # 카테고리별로 가장 구체적인 태그를 가진 프레임의 상품 선택
    # (태그 수가 많을수록 = 더 명확하게 감지된 것)
    best_per_category = {}
    for p in frame_results:
        cat = p.get("category", "")
        if not cat:
            continue
        tags = p.get("detected_tags", [])
        if cat not in best_per_category or len(tags) > len(best_per_category[cat].get("detected_tags", [])):
            best_per_category[cat] = p

    unique = list(best_per_category.values())

    if not unique:
        print("[Vision] 인식된 상품 없음 → 목업 데이터 사용")
        return _mock_products(title, channel)

    # 프레임 이미지를 서빙 가능한 디렉토리로 복사
    if frames_serve_dir:
        os.makedirs(frames_serve_dir, exist_ok=True)
        for p in unique:
            frame_path = p.pop("_frame_path", None)
            if frame_path and os.path.exists(frame_path):
                fname = Path(frame_path).name
                dest = os.path.join(frames_serve_dir, fname)
                shutil.copy2(frame_path, dest)
                p["frame_image"] = f"/stills/{Path(frames_serve_dir).name}/{fname}"
                p["frame_reason"] = f"이 장면에서 {p['category']} 상품이 감지됐습니다"
    else:
        for p in unique:
            p.pop("_frame_path", None)

    return unique


def _analyze_frame(frame_path: str) -> list[dict]:
    """Google Vision API로 단일 프레임 분석"""
    try:
        image_data = encode_image(frame_path)

        request_body = {
            "requests": [{
                "image": {"content": image_data},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 20},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                ]
            }]
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                VISION_URL,
                params={"key": GOOGLE_VISION_API_KEY},
                json=request_body
            )
            data = resp.json()

        if "responses" not in data or not data["responses"]:
            return []

        response = data["responses"][0]
        labels = [l["description"].lower() for l in response.get("labelAnnotations", [])]
        objects = [o["name"].lower() for o in response.get("localizedObjectAnnotations", [])]
        all_tags = list(set(labels + objects))

        products = _tags_to_products(all_tags)
        print(f"[Vision] {Path(frame_path).name} → 태그: {all_tags[:5]} → 상품: {len(products)}개")
        return products

    except Exception as e:
        print(f"[Vision] 프레임 분석 실패 {frame_path}: {e}")
        return []


def _tags_to_products(tags: list[str]) -> list[dict]:
    """Google Vision 태그를 상품 정보로 변환 (한국어 검색어 사용)"""
    products = []
    matched_categories = set()

    for tag in tags:
        for (eng_kw, kor_keyword, category) in PRODUCT_TAG_MAP:
            if category in matched_categories:
                continue
            if eng_kw in tag:
                matched_categories.add(category)
                related = [t for t in tags if any(k in t for k, _, c in PRODUCT_TAG_MAP if c == category)][:3]
                products.append({
                    "name": kor_keyword,
                    "category": category,
                    "description": f"방송 화면에서 '{tag}' 감지",
                    "search_keyword": kor_keyword,
                    "detected_tags": related,
                })
                break

    return products


def _mock_products(title: str, channel: str) -> list[dict]:
    keywords = [w for w in title.replace("-", " ").replace("_", " ").split() if len(w) >= 2]
    defaults = [
        {"name": "캐주얼 오버핏 티셔츠", "category": "의류", "description": "루즈핏 반팔", "search_keyword": "오버핏 티셔츠", "detected_tags": [], "frame_image": "", "frame_reason": "목업 데이터"},
        {"name": "크로스백 숄더백", "category": "가방", "description": "데일리 가방", "search_keyword": "크로스백", "detected_tags": [], "frame_image": "", "frame_reason": "목업 데이터"},
        {"name": "슬림 데님 팬츠", "category": "의류", "description": "스트레이트 청바지", "search_keyword": "슬림 데님 팬츠", "detected_tags": [], "frame_image": "", "frame_reason": "목업 데이터"},
        {"name": "스니커즈 운동화", "category": "신발", "description": "데일리 스니커즈", "search_keyword": "스니커즈", "detected_tags": [], "frame_image": "", "frame_reason": "목업 데이터"},
        {"name": "미니 숄더백", "category": "가방", "description": "체인 숄더백", "search_keyword": "미니 숄더백", "detected_tags": [], "frame_image": "", "frame_reason": "목업 데이터"},
    ]
    if keywords:
        for i in range(len(defaults)):
            kw = keywords[i % len(keywords)]
            defaults[i]["search_keyword"] = f"{kw} {defaults[i]['category']}"
    return defaults
