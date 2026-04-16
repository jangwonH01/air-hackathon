"""
Claude Vision으로 방송 프레임에서 상품을 인식합니다.
"""
import anthropic
import base64
import os
from pathlib import Path


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def recognize_products_from_frames(frame_paths: list[str], title: str = "", channel: str = "") -> list[dict]:
    """
    여러 프레임에서 상품을 인식하고 중복 제거 후 반환합니다.
    API 크레딧이 없으면 제목 기반 목업 데이터를 반환합니다.
    """
    all_products = []

    # 프레임을 최대 10개로 제한 (비용 절감)
    sampled = frame_paths[::max(1, len(frame_paths) // 10)][:10]

    for frame_path in sampled:
        products = _analyze_frame(frame_path)
        all_products.extend(products)

    # 상품명 기준으로 중복 제거
    seen = set()
    unique = []
    for p in all_products:
        key = p.get("name", "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)

    # AI 인식 결과가 없으면 제목 기반 목업 데이터 사용
    if not unique:
        unique = _mock_products(title, channel)

    return unique


def _mock_products(title: str, channel: str) -> list[dict]:
    """제목/채널 기반 목업 상품 데이터"""
    keywords = []
    for word in title.replace("-", " ").replace("_", " ").split():
        if len(word) >= 2:
            keywords.append(word)

    # 기본 카테고리별 샘플 상품
    defaults = [
        {"name": "캐주얼 오버핏 티셔츠", "category": "의류", "description": "루즈핏 반팔", "search_keyword": "오버핏 티셔츠"},
        {"name": "크로스백 숄더백", "category": "가방", "description": "데일리 가방", "search_keyword": "크로스백"},
        {"name": "슬림 데님 팬츠", "category": "의류", "description": "스트레이트 청바지", "search_keyword": "슬림 데님 팬츠"},
        {"name": "스니커즈 운동화", "category": "신발", "description": "데일리 스니커즈", "search_keyword": "스니커즈"},
        {"name": "미니 숄더백", "category": "가방", "description": "체인 숄더백", "search_keyword": "미니 숄더백"},
    ]

    # 키워드가 있으면 검색 키워드에 반영
    if keywords:
        for i, item in enumerate(defaults):
            kw = keywords[i % len(keywords)]
            defaults[i]["search_keyword"] = f"{kw} {item['category']}"

    return defaults


def _analyze_frame(frame_path: str) -> list[dict]:
    """단일 프레임에서 상품 인식"""
    try:
        image_data = encode_image(frame_path)
        ext = Path(frame_path).suffix.lower().lstrip(".")
        media_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": """이 방송 화면에서 구매 가능한 상품을 찾아주세요.
의류, 가방, 신발, 액세서리, 음식, 가전, 생활용품 등 모든 상품을 포함합니다.

각 상품을 아래 JSON 배열 형식으로만 응답하세요. 상품이 없으면 빈 배열 []을 반환하세요.
[
  {
    "name": "상품명 (구체적으로)",
    "category": "카테고리 (의류/가방/신발/액세서리/음식/가전/생활용품/기타)",
    "description": "색상, 스타일 등 특징",
    "search_keyword": "네이버 쇼핑 검색에 쓸 키워드"
  }
]"""
                        }
                    ],
                }
            ],
        )

        text = response.content[0].text.strip()
        # JSON 파싱
        import json
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []

    except Exception as e:
        print(f"[Vision] 프레임 분석 실패 {frame_path}: {e}")
        return []
