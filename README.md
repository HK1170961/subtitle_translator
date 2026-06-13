# Subtitle Translator

基于 PyQt6 + llama-server + Whisper 的本地字幕翻译工具，支持从视频中自动提取字幕并翻译为中文。

## 功能特性

- **字幕翻译** — 通过 llama-server 调用本地大模型翻译字幕，支持批量翻译 + 上下文参考
- **Whisper 字幕提取** — 从视频文件中自动提取字幕（视频→音频→人声分离→转录→SRT）
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

依赖列表：
- PyQt6 >= 6.5.0
- requests >= 2.28.0
- chardet >= 5.0.0
- onnxruntime-gpu >= 1.16.0

### 2. 启动程序

```bash
python -m subtitle_translator.main
```

或双击 `run.bat`（自动检查环境并启动）。

### 3. 单独启动 llama-server

```bash
llama\llama-server.exe -m llama\Sakura-Galtransl-7B-v3.7.gguf --host 127.0.0.1 --port 8080
```

或双击 `start_server.bat`。

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
│   └── whisper_extractor.py   # Whisper 提取流程
├── gui/
│   ├── main_window.py         # 主窗口
│   ├── file_panel.py          # 文件管理面板
│   ├── settings_panel.py      # 设置面板
│   └── styles.py              # UI 样式
├── utils/
│   └── config.py              # 配置管理
└── tools/
    ├── ffmpeg/ffmpeg.exe      # 音视频处理
    ├── whisper/               # Whisper 引擎 + 模型
    └── separate/              # UVR 人声分离工具
```

## 配置说明

### 服务器参数

在设置面板的「llama-server 参数」中输入，支持模板变量 `$port`：

```
-ngl 100 --port $port --temp 0.7 --top-p 0.6 --top-k 20 -n 4096
```

### Whisper 参数

在设置面板的「Whisper 提取」中输入，支持模板变量：

| 变量 | 说明 |
|------|------|
| `$whisper_file` | 模型文件完整路径 |
| `$language` | 语言代码 |
| `$input` | 输入 WAV 文件路径 |
| `$output` | 输出基础路径（无扩展名） |

示例：
```
-m $whisper_file -osrt -l $language -f $input -of $output --vad --vad-model ggml-silero-v5.1.2.bin
```

### 输出文件命名

翻译后的字幕文件命名为 `原名_中文字幕.srt`，重名自动追加 `_1`、`_2` 等后缀。

## 工具调用链

```
视频文件
  → [ffmpeg] .ts 转 .mp4（如果是 .ts 格式）
  → [ffmpeg] 提取 16kHz 单声道 WAV
  → [separate.exe] UVR 人声分离（可选）
  → [whisper-cli] 语音识别转录 → .srt
  → [llama-server] 批量翻译 → 中文字幕
```

## 外部工具

| 工具 | 用途 |
|------|------|
| llama-server.exe | 本地 LLM 推理服务器 |
| whisper-cli.exe | Whisper 语音识别转录 |
| ffmpeg.exe | 音视频处理 |
| separate.exe | UVR 人声分离 |

## 模型下载

本项目需要翻译模型和 Whisper 模型，请手动下载并放置到对应目录。

### 翻译模型（放入 `llama/` 目录）

推荐使用以下任一模型：

| 模型 | 下载地址 | 说明 |
|------|---------|------|
| Sakura-GalTransl-7B-v3.7 | [HuggingFace](https://huggingface.co/SakuraLLM/Sakura-GalTransl-7B-v3.7) | 中日翻译专用，质量最佳 |
| HY-MT2-7B | [ModelScope](https://modelscope.cn/models/Tencent-Hunyuan/Hy-MT2-7B-GGUF) | 腾讯混元，多语言翻译 |

下载后将 `.gguf` 文件放入 `llama/` 目录，程序会自动扫描。

### Whisper 模型（放入 `tools/whisper/` 目录）

| 模型 | 下载地址 | 说明 |
|------|---------|------|
| ggml-large-v3-turbo.bin | [HuggingFace](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin) | 推荐，速度快质量高 |
| ggml-large-v3.bin | [HuggingFace](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin) | 最高质量 |
| ggml-medium.bin | [HuggingFace](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin) | 平衡选择 |

VAD 模型 `ggml-silero-v5.1.2.bin` 已包含在项目中，无需额外下载。

## 配置文件

所有设置保存至 `~/.subtitle_translator/config.json`，下次启动自动恢复。
