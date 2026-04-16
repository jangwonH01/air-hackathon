"""
Claude API로 쇼핑 웹앱 HTML을 자동 생성합니다.
"""
import anthropic
import os
import json


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_shopping_webapp(title: str, channel: str, products: list[dict]) -> str:
    """상품 목록을 받아 TV용 쇼핑 웹앱 HTML을 생성합니다."""

    products_json = json.dumps(products, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""아래 상품 정보를 바탕으로 TV 셋탑박스용 쇼핑 웹앱 HTML을 생성해주세요.

방송명: {title}
채널: {channel}
상품 목록:
{products_json}

요구사항:
- 단일 HTML 파일 (CSS/JS 인라인)
- TV 리모컨으로 조작 가능 (방향키, OK/Enter 키 지원)
- 어두운 배경 (#0F0F1A), 큰 글씨 (최소 18px)
- 상품 카드 그리드 (3열), 포커스 시 강조 효과
- 상품 카드: 이미지, 이름, 가격, 구매 버튼
- 구매 버튼 클릭 시 link URL로 이동
- 상단에 방송명 표시
- 페이지네이션 (한 페이지 6개)
- 완전한 HTML만 응답하세요. 설명 없이 코드만."""
            }
        ],
    )

    html = response.content[0].text.strip()
    # 코드 블록 제거
    if html.startswith("```"):
        lines = html.split("\n")
        html = "\n".join(lines[1:-1])

    return html


def save_webapp(job_id: int, html: str, output_dir: str) -> str:
    """생성된 웹앱을 파일로 저장하고 경로를 반환합니다."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"shop_{job_id}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
