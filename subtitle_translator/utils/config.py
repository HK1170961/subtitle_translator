"""配置管理模块"""

import copy
import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
    },
    "server_args": "-ngl 100 --port $port --temp 0.7 --top-p 0.6 --top-k 20 --repeat-penalty 1.05 -n 4096",
    "translation": {
        "source_lang": "English",
        "target_lang": "简体中文",
        "batch_size": 10,
        "bilingual": False,
        "max_workers": 4,
    },
    "whisper_model": "large-v3-turbo",
    "whisper_lang": "ja",
    "separate_vocals": True,
    "auto_translate": True,
    "ui": {
        "theme": "light",
        "window_width": 1280,
        "window_height": 850,
    },
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".subtitle_translator")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_config_dir():
    """确保配置目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    """加载配置。

    读取失败（文件损坏/权限/编码）时打印告警并回退默认配置，
    避免静默吞掉异常导致用户不知设置"丢失"。
    返回值是深拷贝，不会污染全局 DEFAULT_CONFIG。
    """
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return _merge_config(DEFAULT_CONFIG, loaded)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            # 显式告警而非静默吞掉
            print(f"[config] 配置文件读取失败，回退默认配置: {e}")
        except Exception as e:
            print(f"[config] 配置加载出现未预期错误，回退默认配置: {e}")
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: dict):
    """保存配置"""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _merge_config(default: dict, override: dict) -> dict:
    """递归合并配置（深拷贝，不修改 default 原对象）"""
    result = copy.deepcopy(default)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
