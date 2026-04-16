import { useState } from "react";

export default function Upload({ onSuccess }) {
  const [title, setTitle] = useState("");
  const [channel, setChannel] = useState("");
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [drag, setDrag] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!title || (!file && !url)) return;

    setLoading(true);
    const form = new FormData();
    form.append("title", title);
    form.append("channel", channel);
    if (url) {
      form.append("url", url);
    } else {
      form.append("video", file);
    }

    try {
      const res = await fetch("http://localhost:8000/api/jobs", { method: "POST", body: form });
      if (res.ok) {
        setTitle(""); setChannel(""); setFile(null);
        onSuccess();
      }
    } catch (e) {
      alert("업로드 실패: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "32px", maxWidth: "560px" }}>
      <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "24px" }}>📤 영상 업로드</h2>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div>
          <label style={labelStyle}>방송명 *</label>
          <input value={title} onChange={e => setTitle(e.target.value)}
            placeholder="예: 눈물의 여왕 E16" required style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>채널명</label>
          <input value={channel} onChange={e => setChannel(e.target.value)}
            placeholder="예: KBS2" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>YouTube URL</label>
          <input value={url} onChange={e => { setUrl(e.target.value); setFile(null); }}
            placeholder="https://www.youtube.com/watch?v=..." style={inputStyle} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", color: "#8888AA", fontSize: "0.8rem" }}>
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.1)" }} />
          또는 파일 직접 업로드
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.1)" }} />
        </div>
        <div>
          <label style={labelStyle}>영상 파일</label>
          <div
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) { setFile(f); setUrl(""); } }}
            onClick={() => document.getElementById("fileInput").click()}
            style={{ border: `2px dashed ${drag ? "#6C63FF" : "rgba(255,255,255,0.15)"}`, borderRadius: "10px", padding: "32px", textAlign: "center", cursor: "pointer", background: drag ? "rgba(108,99,255,0.08)" : "transparent", transition: "all 0.2s", opacity: url ? 0.4 : 1 }}>
            <input id="fileInput" type="file" accept="video/*" style={{ display: "none" }} onChange={e => { setFile(e.target.files[0]); setUrl(""); }} />
            {file
              ? <><div style={{ fontSize: "1.5rem" }}>🎬</div><div style={{ marginTop: "8px", fontWeight: 600 }}>{file.name}</div><div style={{ fontSize: "0.8rem", color: "#8888AA" }}>{(file.size / 1024 / 1024).toFixed(1)} MB</div></>
              : <><div style={{ fontSize: "1.5rem" }}>📁</div><div style={{ marginTop: "8px", color: "#8888AA", fontSize: "0.9rem" }}>파일을 드래그하거나 클릭해서 업로드</div></>
            }
          </div>
        </div>
        <button type="submit" disabled={loading || !title || (!file && !url)}
          style={{ background: loading ? "#444" : "#6C63FF", color: "white", border: "none", borderRadius: "8px", padding: "14px", fontWeight: 700, fontSize: "1rem", cursor: loading ? "not-allowed" : "pointer", marginTop: "8px" }}>
          {loading ? "분석 중..." : "⚡ 분석 시작"}
        </button>
      </form>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#8888AA", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" };
const inputStyle = { width: "100%", background: "#1A1A2E", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "12px 14px", color: "#E0E0F0", fontSize: "0.95rem", outline: "none" };
