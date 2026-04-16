const STATUS = {
  pending:    { label: "대기 중",   color: "#8888AA", bg: "rgba(136,136,170,0.1)" },
  processing: { label: "분석 중",   color: "#FF9800", bg: "rgba(255,152,0,0.1)" },
  done:       { label: "완료",      color: "#4CAF50", bg: "rgba(76,175,80,0.1)"  },
  failed:     { label: "실패",      color: "#FF5252", bg: "rgba(255,82,82,0.1)"  },
};

export default function JobList({ jobs, selected, onSelect }) {
  if (!jobs.length) {
    return (
      <div style={{ padding: "60px 32px", textAlign: "center", color: "#8888AA" }}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>🎬</div>
        <div>분석된 방송이 없습니다.<br />영상을 업로드해 주세요.</div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px" }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "16px", color: "#8888AA" }}>방송 목록</h2>
      {jobs.map(job => {
        const s = STATUS[job.status] || STATUS.pending;
        const isSelected = selected?.id === job.id;
        return (
          <div key={job.id} onClick={() => onSelect(job)}
            style={{ background: isSelected ? "rgba(108,99,255,0.12)" : "#1A1A2E", border: `1px solid ${isSelected ? "#6C63FF" : "rgba(255,255,255,0.06)"}`, borderRadius: "12px", padding: "16px 20px", marginBottom: "10px", cursor: "pointer", transition: "all 0.15s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontWeight: 700, marginBottom: "4px" }}>{job.title}</div>
                <div style={{ fontSize: "0.8rem", color: "#8888AA" }}>{job.channel || "채널 미지정"} · {new Date(job.created_at).toLocaleDateString("ko-KR")}</div>
              </div>
              <span style={{ background: s.bg, color: s.color, padding: "3px 10px", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 600, flexShrink: 0 }}>
                {s.label}
              </span>
            </div>
            {job.status === "done" && (
              <div style={{ marginTop: "10px", display: "flex", gap: "12px" }}>
                <span style={{ fontSize: "0.8rem", color: "#6C63FF" }}>🛍 상품 {job.product_count}개</span>
                <span style={{ fontSize: "0.8rem", color: job.popup_enabled === "on" ? "#4CAF50" : "#8888AA" }}>
                  {job.popup_enabled === "on" ? "● 팝업 ON" : "○ 팝업 OFF"}
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
