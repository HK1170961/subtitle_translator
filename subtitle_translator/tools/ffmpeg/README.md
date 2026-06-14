# ffmpeg

将ffmpeg.exe放入此文件夹。

## 获取方式

### 方式一：下载静态构建版（推荐）

1. 访问 https://github.com/BtbN/FFmpeg-Builds/releases
2. 下载 `ffmpeg-master-latest-win64-gpl.zip`
3. 解压后将 `ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe` 放入本目录

### 方式二：通过 winget 安装

```bash
winget install Gyan.FFmpeg
```

安装后将 `ffmpeg.exe` 复制到本目录。

### 方式三：通过 conda 安装

```bash
conda install -c conda-forge ffmpeg
```

## 验证

```bash
ffmpeg -version
```
