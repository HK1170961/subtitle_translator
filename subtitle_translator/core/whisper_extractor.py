import subprocess
import os
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal


BASE_DIR = Path(__file__).parent.parent
FFMPEG_PATH = BASE_DIR / "tools" / "ffmpeg" / "ffmpeg.exe"
WHISPER_CLI_PATH = BASE_DIR / "tools" / "whisper" / "whisper-cli.exe"
WHISPER_MODELS_DIR = BASE_DIR / "tools" / "whisper"
SEPARATE_PATH = BASE_DIR / "tools" / "separate" / "separate.exe"
SEPARATE_INTERNAL_DIR = BASE_DIR / "tools" / "separate" / "_internal"


def convert_ts_to_mp4(ts_path: str, output_dir: str, ffmpeg_path: Optional[str] = None) -> str:
    """使用ffmpeg将.ts转换为.mp4"""
    ffmpeg = ffmpeg_path or str(FFMPEG_PATH)
    if not os.path.exists(ffmpeg):
        raise FileNotFoundError(f"ffmpeg未找到: {ffmpeg}")

    base_name = os.path.splitext(os.path.basename(ts_path))[0]
    mp4_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"[Whisper] 转换 .ts → .mp4: {ts_path}")
    cmd = [ffmpeg, "-i", ts_path, "-c", "copy", "-y", mp4_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f".ts转.mp4失败: {result.stderr[-500:]}")

    print(f"[Whisper] 转换完成: {mp4_path}")
    return mp4_path


def extract_audio(video_path: str, output_wav: str, ffmpeg_path: Optional[str] = None) -> str:
    """从视频中提取16kHz单声道WAV音频"""
    ffmpeg = ffmpeg_path or str(FFMPEG_PATH)
    if not os.path.exists(ffmpeg):
        raise FileNotFoundError(f"ffmpeg未找到: {ffmpeg}")

    cmd = [ffmpeg, "-i", video_path, "-ar", "16000", "-ac", "1", "-f", "wav", "-y", output_wav]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"音频提取失败: {result.stderr[-500:]}")
    return output_wav


def separate_vocals(wav_path: str, output_dir: str, separate_path: Optional[str] = None) -> str:
    """使用UVR分离人声"""
    sep = separate_path or str(SEPARATE_PATH)
    if not os.path.exists(sep):
        raise FileNotFoundError(f"separate.exe未找到: {sep}")

    os.makedirs(output_dir, exist_ok=True)
    model_path = str(BASE_DIR / "tools" / "separate" / "UVR_MDXNET_KARA_2.onnx")

    # separate.exe outputs to the same directory as input by default
    cmd = [sep, "-m", model_path, wav_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=output_dir)
    if result.returncode != 0:
        raise RuntimeError(f"人声分离失败: {result.stderr[-500:]}")

    # 查找输出的人声文件 - 检查输入目录和输出目录
    base_name = os.path.splitext(os.path.basename(wav_path))[0]
    input_dir = os.path.dirname(wav_path)

    for search_dir in [output_dir, input_dir]:
        if not os.path.exists(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.lower().endswith("_vocals.wav") and base_name in f:
                return os.path.join(search_dir, f)

    raise RuntimeError("未找到分离后的人声文件")


def transcribe(wav_path: str, output_dir: str, whisper_cli: Optional[str] = None,
               model: str = "ggml-large-v3-turbo.bin", language: str = "ja",
               custom_args: Optional[str] = None) -> str:
    """使用whisper-cli转录，输出SRT。支持自定义参数"""
    cli = whisper_cli or str(WHISPER_CLI_PATH)
    if not os.path.exists(cli):
        raise FileNotFoundError(f"whisper-cli.exe未找到: {cli}")

    out_base = os.path.splitext(os.path.basename(wav_path))[0]
    out_base_path = os.path.join(output_dir, out_base)

    if custom_args:
        whirl = str(WHISPER_MODELS_DIR)

        # 第一步：按空格分割模板（保留引号内的空格），得到原始token列表
        raw_tokens = []
        buf = []
        in_q = False
        for c in custom_args:
            if c == '"':
                in_q = not in_q
                buf.append(c)
            elif c in (' ', '\t') and not in_q:
                if buf:
                    raw_tokens.append(''.join(buf))
                    buf = []
            else:
                buf.append(c)
        if buf:
            raw_tokens.append(''.join(buf))

        # 第二步：对每个token分别进行变量替换 + 路径转换
        expanded = []
        for token in raw_tokens:
            t = token

            # 首先处理 whisper/ 相对路径（避免污染后面的变量展开值）
            t = t.replace("whisper/", f"{whirl}/")
            t = t.replace("whisper\\", f"{whirl}\\")

            # 然后进行变量替换
            t = t.replace("$input_file", wav_path)
            t = t.replace("$whisper_file", str(WHISPER_MODELS_DIR / model))
            t = t.replace("$input", wav_path)
            t = t.replace("$output", out_base_path)
            t = t.replace("$language", language)

            # 去掉开头的可执行路径（如果用户包含了）
            t_stripped = t.strip()
            lower_t = t_stripped.lower()
            lower_cli = cli.lower()
            if lower_t == lower_cli or lower_t.startswith(lower_cli + " "):
                continue
            t_cli_path = "whisper-cli"
            if t_cli_path in lower_t and (lower_t.endswith(t_cli_path) or lower_t.endswith(t_cli_path + ".exe")):
                continue

            expanded.append(t_stripped)

        cmd_str = f'"{cli}" {" ".join(expanded)}'
        print(f"[Whisper] 执行命令: {cmd_str}")
        cmd = [cli] + expanded
    else:
        vad_model = str(WHISPER_MODELS_DIR / "ggml-silero-v5.1.2.bin")
        cmd = [
            cli, "-m", str(WHISPER_MODELS_DIR / model),
            "-osrt", "-l", language,
            "--vad", "--vad-model", vad_model,
            "-f", wav_path,
            "-of", out_base_path
        ]

    print(f"[Whisper] 执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(WHISPER_MODELS_DIR))
    print(f"[Whisper] stdout: {result.stdout[:500] if result.stdout else ''}")
    if result.stderr:
        print(f"[Whisper] stderr: {result.stderr[:500]}")
    if result.returncode != 0:
        raise RuntimeError(f"Whisper转录失败: {result.stderr[-500:]}")

    srt_path = out_base_path + ".srt"
    if os.path.exists(srt_path):
        print(f"[Whisper] 转录完成: {srt_path}")
        return srt_path
    raise RuntimeError("未生成SRT文件")


def extract_subtitles(video_path: str, output_dir: str, model: str, language: str,
                       separate: bool = True, whisper_cli: Optional[str] = None,
                       custom_args: Optional[str] = None) -> str:
    """完整流程: 视频→人声分离(可选)→转录→SRT"""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    print(f"[Whisper] 开始提取: {video_path}")
    print(f"[Whisper] 输出目录: {output_dir}")
    print(f"[Whisper] 模型: {model}, 语言: {language}, 人声分离: {separate}")

    # Step 0: 如果是.ts文件，先转换为.mp4
    actual_video_path = video_path
    if video_path.lower().endswith(".ts"):
        print(f"[Whisper] Step 0: 检测到.ts文件，转换为.mp4...")
        actual_video_path = convert_ts_to_mp4(video_path, output_dir)

    # Step 1: 提取音频
    print(f"[Whisper] Step 1: 提取音频...")
    wav_path = os.path.join(output_dir, f"{base_name}_audio.wav")
    extract_audio(actual_video_path, wav_path)
    print(f"[Whisper] 音频提取完成: {wav_path}")

    # Step 2: 人声分离(可选)
    if separate:
        print(f"[Whisper] Step 2: 人声分离...")
        vocal_dir = os.path.join(output_dir, "vocal_separate")
        vocal_path = separate_vocals(wav_path, vocal_dir)
        print(f"[Whisper] 人声分离完成: {vocal_path}")
    else:
        vocal_path = wav_path
        print(f"[Whisper] Step 2: 跳过人声分离")

    # Step 3: Whisper转录
    print(f"[Whisper] Step 3: Whisper转录...")
    srt_path = transcribe(vocal_path, output_dir, whisper_cli, model, language, custom_args)
    print(f"[Whisper] 转录完成: {srt_path}")
    return srt_path


class WhisperWorker(QThread):
    """后台执行Whisper提取"""
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, video_path, output_dir, model, language, separate, custom_args=None):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.model = model
        self.language = language
        self.separate = separate
        self.custom_args = custom_args

    def run(self):
        try:
            self.progress.emit("正在从视频中提取音频...")
            srt_path = extract_subtitles(
                self.video_path, self.output_dir,
                self.model, self.language, self.separate,
                custom_args=self.custom_args
            )
            self.finished.emit(srt_path)
        except Exception as e:
            self.error.emit(str(e))
