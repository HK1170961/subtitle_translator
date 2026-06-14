# separate (UVR 人声分离)

Ultimate Vocal Remover 人声分离工具，用于从音频中分离人声与伴奏。

## 获取方式

### 方式一：下载预编译版（推荐）

1. 访问 https://github.com/Anjok07/ultimatevocalremovergui/releases
2. 下载最新版本的 `UVR_*_setup_*.exe` 安装包
3. 安装后找到安装目录，将以下文件复制到本目录：
   - `separate.exe`
   - `UVR_MDXNET_KARA_2.onnx`（模型文件，通常在 `models/` 目录下）
   - `_internal/` 文件夹（PyInstaller 运行时依赖）

### 方式二：从本项目备份获取

如果已有人分享了工具文件，直接将以下文件放入本目录：
- `separate.exe`
- `UVR_MDXNET_KARA_2.onnx`
- `_internal/` 文件夹

## 目录结构

```
separate/
├── README.md                    # 本文件
├── separate.exe                 # 主程序
├── UVR_MDXNET_KARA_2.onnx      # 分离模型
└── _internal/                   # PyInstaller 运行时依赖
    ├── ...
```

## 验证

```bash
separate.exe --help
```
