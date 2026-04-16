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


def recognize_products_from_frames(frame_paths: list[str]) -> list[dict]:
    """
    여러 프레임에서 상품을 인식하고 중복 제거 후 반환합니다.
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

    return unique


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
