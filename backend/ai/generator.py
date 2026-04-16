"""
Claude API로 쇼핑 웹앱 HTML을 자동 생성합니다.
"""
import anthropic
import os
import json


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_shopping_webapp(title: str, channel: str, products: list[dict]) -> str:
    """상품 목록을 받아 TV용 쇼핑 웹앱 HTML을 생성합니다."""
    products_json = json.dumps(products, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <title>{title} - AIR 쇼핑</title>
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:#0F0F1A;color:#E0E0F0;font-family:sans-serif;min-height:100vh;}}
    header{{background:#1A1A2E;padding:20px 40px;border-bottom:1px solid rgba(108,99,255,0.3);display:flex;align-items:center;gap:16px;}}
    header h1{{font-size:1.4rem;font-weight:800;color:#6C63FF;}}
    header span{{font-size:0.9rem;color:#8888AA;}}
    .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:32px 40px;}}
    .card{{background:#1A1A2E;border:2px solid rgba(255,255,255,0.06);border-radius:14px;overflow:hidden;cursor:pointer;transition:all 0.15s;}}
    .card.focused{{border-color:#6C63FF;transform:scale(1.03);outline:none;}}
    .card img{{width:100%;aspect-ratio:1;object-fit:cover;background:#111;}}
    .card-body{{padding:14px 16px;}}
    .card-name{{font-size:1rem;font-weight:600;margin-bottom:6px;}}
    .card-cat{{font-size:0.8rem;color:#8888AA;margin-bottom:8px;}}
    .card-price{{font-size:1.1rem;font-weight:800;color:#FF6584;}}
    .card-mall{{font-size:0.75rem;color:#8888AA;margin-top:4px;}}
    .pagination{{display:flex;justify-content:center;gap:12px;padding:0 40px 32px;}}
    .page-btn{{background:rgba(108,99,255,0.15);border:1px solid #6C63FF;color:#6C63FF;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:0.9rem;font-weight:600;}}
    .page-btn:disabled{{opacity:0.3;cursor:default;}}
    .no-image{{width:100%;aspect-ratio:1;background:#1A1A2E;display:flex;align-items:center;justify-content:center;font-size:3rem;}}
  </style>
</head>
<body>
<div id="app">
  <header>
    <h1>🛍 AIR</h1>
    <span>'{{{{ title }}}}'에서 발견한 상품 {{{{ total }}}}개</span>
    <span style="margin-left:auto;font-size:0.8rem;">{{{{ channel }}}}</span>
  </header>
  <div class="grid">
    <div v-for="(p, i) in pageProducts" :key="i"
      class="card" :class="{{focused: focusIdx === pageStart + i}}"
      @click="open(p)" tabindex="0">
      <img v-if="p.image" :src="p.image" :alt="p.name" @error="e=>e.target.style.display='none'"/>
      <div v-else class="no-image">🛒</div>
      <div class="card-body">
        <div class="card-name">{{{{ p.name }}}}</div>
        <div class="card-cat">{{{{ p.category }}}}</div>
        <div class="card-price" v-if="p.price > 0">{{{{ p.price.toLocaleString() }}}}원</div>
        <div class="card-mall">{{{{ p.mall }}}}</div>
      </div>
    </div>
  </div>
  <div class="pagination" v-if="totalPages > 1">
    <button class="page-btn" :disabled="page===0" @click="page--">◀ 이전</button>
    <span style="line-height:2.4;color:#8888AA">{{{{ page+1 }}}} / {{{{ totalPages }}}}</span>
    <button class="page-btn" :disabled="page===totalPages-1" @click="page++">다음 ▶</button>
  </div>
</div>
<script>
const {{ createApp, ref, computed, onMounted, onUnmounted }} = Vue;
createApp({{
  setup() {{
    const products = {products_json};
    const title = {json.dumps(title, ensure_ascii=False)};
    const channel = {json.dumps(channel or "", ensure_ascii=False)};
    const PER_PAGE = 6;
    const page = ref(0);
    const focusIdx = ref(0);
    const total = computed(() => products.length);
    const totalPages = computed(() => Math.ceil(products.length / PER_PAGE));
    const pageStart = computed(() => page.value * PER_PAGE);
    const pageProducts = computed(() => products.slice(pageStart.value, pageStart.value + PER_PAGE));
    function open(p) {{ if (p.link) window.open(p.link, '_blank'); }}
    function onKey(e) {{
      const len = pageProducts.value.length;
      if (e.key==='ArrowRight') focusIdx.value = Math.min(focusIdx.value+1, pageStart.value+len-1);
      else if (e.key==='ArrowLeft') focusIdx.value = Math.max(focusIdx.value-1, pageStart.value);
      else if (e.key==='ArrowDown') focusIdx.value = Math.min(focusIdx.value+3, pageStart.value+len-1);
      else if (e.key==='ArrowUp') focusIdx.value = Math.max(focusIdx.value-3, pageStart.value);
      else if (e.key==='Enter') open(products[focusIdx.value]);
      else if (e.key==='PageDown' && page.value < totalPages.value-1) {{ page.value++; focusIdx.value = pageStart.value; }}
      else if (e.key==='PageUp' && page.value > 0) {{ page.value--; focusIdx.value = pageStart.value; }}
    }}
    onMounted(() => window.addEventListener('keydown', onKey));
    onUnmounted(() => window.removeEventListener('keydown', onKey));
    return {{ products, title, channel, total, page, totalPages, pageStart, pageProducts, focusIdx, open }};
  }}
}}).mount('#app');
</script>
</body>
</html>"""


def save_webapp(job_id: int, html: str, output_dir: str) -> str:
    """생성된 웹앱을 파일로 저장하고 경로를 반환합니다."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"shop_{job_id}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
