import { useState, useEffect } from "react";
import Upload from "./components/Upload";
import JobList from "./components/JobList";
import JobDetail from "./components/JobDetail";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [tab, setTab] = useState("list"); // list | upload

  const fetchJobs = async () => {
    const res = await fetch("http://localhost:8000/api/jobs");
    const data = await res.json();
    setJobs(data);
    setSelected(prev => prev ? (data.find(j => j.id === prev.id) ?? prev) : null);
  };

  useEffect(() => {
    fetchJobs();
    const timer = setInterval(fetchJobs, 3000); // 3초마다 갱신
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#0F0F1A", color: "#E0E0F0", fontFamily: "sans-serif" }}>
      {/* 헤더 */}
      <div style={{ background: "#1A1A2E", borderBottom: "1px solid rgba(108,99,255,0.2)", padding: "16px 32px", display: "flex", alignItems: "center", gap: "24px" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#6C63FF", margin: 0 }}>AIR <span style={{ color: "#FF6584" }}>Admin</span></h1>
        <nav style={{ display: "flex", gap: "16px" }}>
          {["list", "upload"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              style={{ background: tab === t ? "rgba(108,99,255,0.2)" : "transparent", border: "1px solid", borderColor: tab === t ? "#6C63FF" : "transparent", color: tab === t ? "#6C63FF" : "#8888AA", padding: "6px 16px", borderRadius: "6px", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem" }}>
              {t === "list" ? "📋 방송 목록" : "📤 영상 업로드"}
            </button>
          ))}
        </nav>
        <span style={{ marginLeft: "auto", fontSize: "0.8rem", color: "#8888AA" }}>총 {jobs.length}개 방송</span>
      </div>

      {/* 본문 */}
      <div style={{ display: "flex", height: "calc(100vh - 65px)" }}>
        {/* 좌측 패널 */}
        <div style={{ width: selected ? "380px" : "100%", borderRight: "1px solid rgba(255,255,255,0.06)", overflowY: "auto", transition: "width 0.2s" }}>
          {tab === "upload"
            ? <Upload onSuccess={() => { fetchJobs(); setTab("list"); }} />
            : <JobList jobs={jobs} selected={selected} onSelect={setSelected} />
          }
        </div>

        {/* 우측 상세 */}
        {selected && (
          <div style={{ flex: 1, overflowY: "auto" }}>
            <JobDetail job={selected} onRefresh={fetchJobs} onClose={() => setSelected(null)} onDelete={() => { setSelected(null); fetchJobs(); }} />
          </div>
        )}
      </div>
    </div>
  );
}
