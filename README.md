# Subtitle Translator

基于 PyQt6 + llama-server + Faster-Whisper 的本地字幕翻译工具，支持从视频中自动提取字幕并翻译为中文。

## 功能特性

- **字幕翻译** — 通过 llama-server 调用本地大模型翻译字幕，支持批量翻译 + 上下文参考
- **Whisper 字幕提取** — 使用 faster-whisper Python API 从视频文件中自动提取字幕（视频→音频→人声分离→转录→SRT）
- **UVR 人声分离** — 使用 UVR MDXNET 分离人声与伴奏，提升转录准确度
- **双语字幕** — 支持生成原文+译文双语字幕（SRT/ASS 格式）
- **多格式支持** — 字幕：SRT、ASS/SSA；视频：MP4、MKV、AVI、WebM、TS、MOV
- **多语言翻译** — 支持 12 种语言互译
- **拖拽导入** — 支持拖拽导入字幕和视频文件
- **自动服务器管理** — 翻译时自动启动 llama-server，关闭程序时自动终止
- **.ts 格式支持** — 自动检测 .ts 文件并转换为 .mp4 后提取
- **缓存自动清理** — 翻译完成后自动删除 Whisper 中间文件

## 快速开始

### 1. 安装依赖

```bash
pip install -r subtitle_translator/requirements.txt
```

或双击 `run.bat`（自动安装依赖并启动）。

依赖列表：
- PyQt6 >= 6.5.0
- requests >= 2.28.0
- chardet >= 5.0.0
- faster-whisper >= 1.0.0

### 2. 准备工具

将以下工具放入对应目录：

```
项目根目录/
├── llama/
│   ├── llama-server.exe         # llama.cpp 服务器
│   ├── *.dll                    # 运行时依赖
│   └── *.gguf                   # 翻译模型（需手动下载）
└── subtitle_translator/
    └── tools/
        ├── ffmpeg/
        │   └── ffmpeg.exe       # 音视频处理
        └── separate/
            ├── separate.exe     # UVR 人声分离工具
            ├── UVR_MDXNET_KARA_2.onnx  # 分离模型
            └── _internal/       # PyInstaller 运行时依赖
```

### 3. 启动程序

```bash
python -m subtitle_translator.main
```

或双击 `run.bat`。

## 项目结构

```
subtitle_translator/
├── main.py                    # 主入口
├── requirements.txt           # Python 依赖
├── core/
│   ├── translator.py          # llama-server API 翻译引擎
│   ├── srt_parser.py          # SRT 字幕解析
│   ├── ass_parser.py          # ASS/SSA 字幕解析
│   ├── batch_processor.py     # 批量翻译工作线程
│   └── whisper_extractor.py   # Whisper 提取流程（faster-whisper API）
├── gui/
│   ├── main_window.py         # 主窗口
│   ├── file_panel.py          # 文件管理面板
│   ├── settings_panel.py      # 设置面板
│   └── styles.py              # UI 样式
├── utils/
│   └── config.py              # 配置管理
└── tools/
    ├── ffmpeg/ffmpeg.exe      # 音视频处理
    └── separate/              # UVR 人声分离工具
```

## 配置说明

### 服务器参数

在设置面板的「llama-server 参数」中输入，支持模板变量 `$port`：

```
-ngl 100 --port $port --temp 0.7 --top-p 0.6 --top-k 20 -n 4096
```

### Whisper 参数

在设置面板的「Whisper 提取」中选择模型与语言：

| 模型 | 说明 |
|------|------|
| large-v3-turbo | 推荐，速度快质量高 |
| large-v3 | 最高质量 |
| medium | 平衡选择 |
| small | 轻量 |
| base | 最小可用 |
| tiny | 速度最快，质量有限 |

模型**首次使用时自动从 HuggingFace 下载**（需联网），缓存后离线可用。
国内网络可使用 hf-mirror.com 镜像站。

语言可选 `ja/en/zh/ko/auto`。

### 输出文件命名

- 提取的字幕文件：`原名.srt`
- 翻译后的字幕文件：`原名_中文字幕.srt`
- 重名自动追加 `_1`、`_2` 等后缀

## 工具调用链

```
视频文件
  → [ffmpeg] .ts 转 .mp4（如果是 .ts 格式）
  → [ffmpeg] 提取 16kHz 单声道 WAV
  → [separate.exe] UVR 人声分离（可选）
  → [faster-whisper] Python API 语音识别转录 → .srt
  → [llama-server] 批量翻译 → 中文字幕
```

## 外部工具

| 工具 | 用途 |
|------|------|
| llama-server.exe | 本地 LLM 推理服务器 |
| faster-whisper | Python API 语音识别转录（CTranslate2 后端，自动下载模型） |
| ffmpeg.exe | 音视频处理 |
| separate.exe | UVR 人声分离 |

## 模型下载

### 翻译模型（放入 `llama/` 目录）

推荐使用以下任一模型：

| 模型 | 下载地址 | 说明 |
|------|---------|------|
| Sakura-GalTransl-7B-v3.7 | [HuggingFace](https://huggingface.co/SakuraLLM/Sakura-GalTransl-7B-v3.7) | 中日翻译专用，质量最佳 |
| HY-MT2-7B | [ModelScope](https://modelscope.cn/models/Tencent-Hunyuan/Hy-MT2-7B-GGUF) | 腾讯混元，多语言翻译 |

下载后将 `.gguf` 文件放入 `llama/` 目录，程序会自动扫描。

### Whisper 模型（自动下载）

Faster-Whisper 模型在首次使用时**自动从 HuggingFace 下载**，无需手动操作。

| 模型 | 来源 | 说明 |
|------|------|------|
| large-v3-turbo | [Systran/faster-whisper-large-v3-turbo](https://huggingface.co/Systran/faster-whisper-large-v3-turbo) | 推荐，速度快质量高 |
| large-v3 | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | 最高质量 |
| medium | [Systran/faster-whisper-medium](https://huggingface.co/Systran/faster-whisper-medium) | 平衡选择 |

下载后缓存至 `~/.cache/huggingface/hub/`，之后离线可用。

## 配置文件

所有设置保存至 `~/.subtitle_translator/config.json`，下次启动自动恢复。
