"""Whisper 提取模块 - 使用 faster-whisper Python API"""

import os
import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

# 设置 HuggingFace 镜像站
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

BASE_DIR = Path(__file__).parent.parent
FFMPEG_PATH = BASE_DIR / "tools" / "ffmpeg" / "ffmpeg.exe"
SEPARATE_PATH = BASE_DIR / "tools" / "separate" / "separate.exe"

# 将 llama 目录加入 PATH，确保 ctranslate2 能找到 cuBLAS DLL
_llama_dir = str(BASE_DIR.parent / "llama")
if _llama_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _llama_dir + os.pathsep + os.environ.get("PATH", "")

_model_cache: dict = {}
_segments_cache: list = []


def _get_model(model_name: str, device: str = "cuda", compute_type: str = "float16"):
    """获取或缓存 WhisperModel 实例"""
    cache_key = f"{model_name}|{device}|{compute_type}"
    if cache_key not in _model_cache:
        print(f"[Whisper] 加载模型: {model_name} (首次加载约10-30秒)")
        from faster_whisper import WhisperModel
        _model_cache[cache_key] = WhisperModel(
            model_name, device=device, compute_type=compute_type
        )
        print(f"[Whisper] 模型加载完成")
    return _model_cache[cache_key]


def _format_timestamp(seconds: float) -> str:
    """将秒数转换为 SRT 时间戳格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _segments_to_srt(segments: list) -> str:
    """将 segments 转换为 SRT 格式字符串"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp(seg["start"])
        end = _format_timestamp(seg["end"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"].strip())
        lines.append("")
    return "\n".join(lines)


def _parse_segments(raw_segments) -> list:
    """解析 faster-whisper 输出的 segments 生成器，逐条打印进度"""
    global _segments_cache
    _segments_cache = []
    for seg in raw_segments:
        _segments_cache.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
        })
        print(f"[Whisper] 片段 {len(_segments_cache)}: {seg.start:.1f}s-{seg.end:.1f}s  {seg.text[:80]}")
    return _segments_cache


def get_segments() -> list:
    return _segments_cache


def convert_ts_to_mp4(ts_path: str, output_dir: str, ffmpeg_path: Optional[str] = None) -> str:
    import subprocess
    ffmpeg = ffmpeg_path or str(FFMPEG_PATH)
    if not os.path.exists(ffmpeg):
        raise FileNotFoundError(f"ffmpeg未找到: {ffmpeg}")

    base_name = os.path.splitext(os.path.basename(ts_path))[0]
    mp4_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"[Whisper] 转换 .ts → .mp4: {ts_path}")
    cmd = [ffmpeg, "-i", ts_path, "-c", "copy", "-y", mp4_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        err = (result.stderr or "")[-500:]
        raise RuntimeError(f".ts转.mp4失败: {err}")

    print(f"[Whisper] 转换完成: {mp4_path}")
    return mp4_path


def extract_audio(video_path: str, output_wav: str, ffmpeg_path: Optional[str] = None) -> str:
    import subprocess
    ffmpeg = ffmpeg_path or str(FFMPEG_PATH)
    if not os.path.exists(ffmpeg):
        raise FileNotFoundError(f"ffmpeg未找到: {ffmpeg}")

    cmd = [ffmpeg, "-i", video_path, "-ar", "16000", "-ac", "1", "-f", "wav", "-y", output_wav]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        err = (result.stderr or "")[-500:]
        raise RuntimeError(f"音频提取失败: {err}")
    return output_wav


def separate_vocals(wav_path: str, output_dir: str, separate_path: Optional[str] = None) -> str:
    import subprocess
    sep = separate_path or str(SEPARATE_PATH)
    if not os.path.exists(sep):
        raise FileNotFoundError(f"separate.exe未找到: {sep}")

    os.makedirs(output_dir, exist_ok=True)
    model_path = str(BASE_DIR / "tools" / "separate" / "UVR_MDXNET_KARA_2.onnx")

    cmd = [sep, "-m", model_path, wav_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=output_dir)
    if result.returncode != 0:
        err = (result.stderr or "")[-500:]
        raise RuntimeError(f"人声分离失败: {err}")

    base_name = os.path.splitext(os.path.basename(wav_path))[0]
    input_dir = os.path.dirname(wav_path)

    for search_dir in [output_dir, input_dir]:
        if not os.path.exists(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.lower().endswith("_vocals.wav") and base_name in f:
                return os.path.join(search_dir, f)

    raise RuntimeError("未找到分离后的人声文件")


def transcribe(wav_path: str, output_dir: str, model_name: str = "large-v3-turbo",
               language: str = "ja", use_vad: bool = True,
               output_name: str = "") -> str:
    """使用 faster-whisper Python API 转录，输出 SRT"""

    os.makedirs(output_dir, exist_ok=True)

    print(f"[Whisper] 使用 faster-whisper Python API 转录")
    print(f"[Whisper] 模型: {model_name}, 语言: {language}, VAD: {use_vad}")

    whisper_model = _get_model(model_name)

    lang = language if language and language != "auto" else "ja"

    raw_segments, info = whisper_model.transcribe(
        wav_path,
        task="transcribe",
        language=lang,
        vad_filter=use_vad,
        vad_parameters=dict(min_silence_duration_ms=500),
        beam_size=3,
        condition_on_previous_text=False,
    )

    print(f"[Whisper] 检测到语言: {info.language} (概率: {info.language_probability:.2f})")

    segments = _parse_segments(raw_segments)
    print(f"[Whisper] 共 {len(segments)} 个文本片段")

    srt_content = _segments_to_srt(segments)
    srt_name = output_name if output_name else os.path.splitext(os.path.basename(wav_path))[0]
    srt_path = os.path.join(output_dir, f"{srt_name}.srt")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"[Whisper] 转录完成: {srt_path}")
    return srt_path


def extract_subtitles(video_path: str, output_dir: str, model: str, language: str,
                       separate: bool = True, use_vad: bool = True) -> str:
    """完整流程: 视频→人声分离(可选)→转录→SRT"""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    print(f"[Whisper] 开始提取: {video_path}")
    print(f"[Whisper] 输出目录: {output_dir}")
    print(f"[Whisper] 模型: {model}, 语言: {language}, 人声分离: {separate}")

    actual_video_path = video_path
    if video_path.lower().endswith(".ts"):
        print(f"[Whisper] Step 0: 检测到.ts文件，转换为.mp4...")
        actual_video_path = convert_ts_to_mp4(video_path, output_dir)

    print(f"[Whisper] Step 1: 提取音频...")
    wav_path = os.path.join(output_dir, f"{base_name}_audio.wav")
    extract_audio(actual_video_path, wav_path)
    print(f"[Whisper] 音频提取完成: {wav_path}")

    if separate:
        print(f"[Whisper] Step 2: 人声分离...")
        vocal_dir = os.path.join(output_dir, "vocal_separate")
        vocal_path = separate_vocals(wav_path, vocal_dir)
        print(f"[Whisper] 人声分离完成: {vocal_path}")
    else:
        vocal_path = wav_path
        print(f"[Whisper] Step 2: 跳过人声分离")

    print(f"[Whisper] Step 3: Whisper转录...")
    srt_path = transcribe(vocal_path, output_dir, model, language, use_vad, output_name=base_name)
    print(f"[Whisper] 转录完成: {srt_path}")
    return srt_path


class WhisperWorker(QThread):
    """后台执行Whisper提取"""
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, video_path, output_dir, model, language, separate, use_vad=True):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.model = model
        self.language = language
        self.separate = separate
        self.use_vad = use_vad

    def run(self):
        try:
            self.progress.emit("正在从视频中提取音频...")
            srt_path = extract_subtitles(
                self.video_path, self.output_dir,
                self.model, self.language, self.separate,
                use_vad=self.use_vad
            )
            self.finished.emit(srt_path)
        except Exception as e:
            self.error.emit(str(e))
