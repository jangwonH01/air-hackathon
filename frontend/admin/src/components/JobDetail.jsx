import { useState } from "react";

export default function JobDetail({ job, onRefresh, onClose }) {
  const [toggling, setToggling] = useState(false);

  const togglePopup = async () => {
    setToggling(true);
    const next = job.popup_enabled !== "on";
    await fetch(`http://localhost:8000/api/jobs/${job.id}/popup?enabled=${next}`, { method: "PATCH" });
    await onRefresh();
    setToggling(false);
  };

  return (
    <div style={{ padding: "32px" }}>
      {/* 헤더 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
        <div>
          <h2 style={{ fontSize: "1.3rem", fontWeight: 700, marginBottom: "4px" }}>{job.title}</h2>
          <span style={{ fontSize: "0.85rem", color: "#8888AA" }}>{job.channel || "채널 미지정"}</span>
        </div>
        <button onClick={onClose} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#8888AA", borderRadius: "6px", padding: "6px 12px", cursor: "pointer", fontSize: "0.8rem" }}>✕ 닫기</button>
      </div>

      {/* 상태 카드 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "12px", marginBottom: "24px" }}>
        <StatCard label="상태" value={job.status === "done" ? "✅ 완료" : job.status === "processing" ? "⏳ 분석 중" : job.status} />
        <StatCard label="인식 상품" value={`${job.product_count}개`} />
        <StatCard label="팝업" value={job.popup_enabled === "on" ? "ON" : "OFF"} valueColor={job.popup_enabled === "on" ? "#4CAF50" : "#8888AA"} />
      </div>

      {/* 팝업 토글 */}
      {job.status === "done" && (
        <div style={{ display: "flex", gap: "12px", marginBottom: "28px" }}>
          <button onClick={togglePopup} disabled={toggling}
            style={{ background: job.popup_enabled === "on" ? "rgba(255,82,82,0.15)" : "rgba(76,175,80,0.15)", border: `1px solid ${job.popup_enabled === "on" ? "#FF5252" : "#4CAF50"}`, color: job.popup_enabled === "on" ? "#FF5252" : "#4CAF50", borderRadius: "8px", padding: "10px 20px", cursor: "pointer", fontWeight: 600, fontSize: "0.9rem" }}>
            {job.popup_enabled === "on" ? "팝업 끄기" : "팝업 켜기"}
          </button>
          {job.webapp_url && (
            <a href={`http://localhost:8000${job.webapp_url}`} target="_blank" rel="noreferrer"
              style={{ background: "rgba(108,99,255,0.15)", border: "1px solid #6C63FF", color: "#6C63FF", borderRadius: "8px", padding: "10px 20px", textDecoration: "none", fontWeight: 600, fontSize: "0.9rem" }}>
              🛍 쇼핑 웹앱 열기
            </a>
          )}
        </div>
      )}

      {/* 상품 목록 */}
      {job.products?.length > 0 && (
        <>
          <h3 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#8888AA", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "0.5px" }}>인식된 상품</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "12px" }}>
            {job.products.map((p, i) => (
              <a key={i} href={p.link} target="_blank" rel="noreferrer"
                style={{ background: "#1A1A2E", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", overflow: "hidden", textDecoration: "none", color: "inherit", display: "block", transition: "border-color 0.15s" }}>
                {p.image && <img src={p.image} alt={p.name} style={{ width: "100%", aspectRatio: "1", objectFit: "cover" }} />}
                <div style={{ padding: "10px 12px" }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "4px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.name}</div>
                  <div style={{ fontSize: "0.75rem", color: "#8888AA", marginBottom: "4px" }}>{p.category}</div>
                  {p.price > 0 && <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#FF6584" }}>{p.price.toLocaleString()}원</div>}
                </div>
              </a>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, valueColor = "#E0E0F0" }) {
  return (
    <div style={{ background: "#1A1A2E", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "14px 16px" }}>
      <div style={{ fontSize: "0.7rem", color: "#8888AA", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>{label}</div>
      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: valueColor }}>{value}</div>
    </div>
  );
}
