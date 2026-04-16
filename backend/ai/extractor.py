"""
ffmpeg으로 영상에서 프레임을 추출합니다.
"""
import subprocess
import os
from pathlib import Path


def extract_frames(video_path: str, output_dir: str, fps: float = 0.5) -> list[str]:
    """
    영상에서 프레임을 추출합니다.
    fps=0.5 → 2초마다 1장 추출
    """
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",          # 품질 (낮을수록 고품질)
        "-y",                  # 덮어쓰기
        output_pattern
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 오류: {result.stderr}")

    frames = sorted(Path(output_dir).glob("frame_*.jpg"))
    return [str(f) for f in frames]
