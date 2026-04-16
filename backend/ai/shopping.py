"""
네이버 쇼핑 API로 인식된 상품을 매칭합니다.
"""
import httpx
import os


NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"


async def match_products(products: list[dict]) -> list[dict]:
    """인식된 상품 목록에 네이버 쇼핑 상품 정보를 매칭합니다."""
    matched = []
    async with httpx.AsyncClient() as client:
        for product in products:
            result = await _search_product(client, product)
            if result:
                matched.append(result)
    return matched


async def _search_product(client: httpx.AsyncClient, product: dict) -> dict | None:
    """단일 상품 검색"""
    try:
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        params = {
            "query": product.get("search_keyword", product.get("name")),
            "display": 3,
            "sort": "sim",
        }
        resp = await client.get(NAVER_SEARCH_URL, headers=headers, params=params, timeout=5.0)
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        top = items[0]
        return {
            "name": _clean_html(top.get("title", product["name"])),
            "category": product.get("category", "기타"),
            "description": product.get("description", ""),
            "price": int(top.get("lprice", 0)),
            "image": top.get("image", ""),
            "link": top.get("link", ""),
            "mall": top.get("mallName", ""),
            "search_keyword": product.get("search_keyword", ""),
        }

    except Exception as e:
        print(f"[Shopping] 상품 검색 실패 {product.get('name')}: {e}")
        # API 실패 시 기본 정보만 반환
        return {
            "name": product.get("name", ""),
            "category": product.get("category", "기타"),
            "description": product.get("description", ""),
            "price": 0,
            "image": "",
            "link": f"https://search.shopping.naver.com/search/all?query={product.get('search_keyword', '')}",
            "mall": "네이버쇼핑",
            "search_keyword": product.get("search_keyword", ""),
        }


def _clean_html(text: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', text)
