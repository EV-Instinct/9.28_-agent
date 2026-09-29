"""
系统全局配置模块
支持环境加载、LLM 提供商配置、Edge-TTS 音色设置、断网离线兜底策略
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 环境变量
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 基础路径
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_DIR = BASE_DIR / "static" / "audio"
IMAGES_DIR = BASE_DIR / "static" / "images"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def get_config_val(key: str, default: str = "") -> str:
    """优先从环境变量读取，云平台部署时兜底支持 streamlit secrets"""
    val = os.getenv(key)
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return val if val else default

# LLM 默认配置 (阿里云百炼 DashScope OpenAI 兼容模式)
DEFAULT_API_BASE = get_config_val("LLM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_API_KEY = get_config_val("LLM_API_KEY", "")
DEFAULT_MODEL = get_config_val("LLM_MODEL", "qwen-plus")

# 语音音色配置 (阿里百炼 CosyVoice 云端大模型纯男声音色)
# longfei: 激情豪迈·古诗吟诵专长男声 (最契合李白诗仙豪气，默认推荐)
# longcheng: 阳光洒脱·意气风发青年男声 (25岁李白仗剑出蜀)
# longshuo: 沉稳英挺·名家风范男声
# longze: 温润清朗·热忱少年男声
DEFAULT_TTS_VOICE = os.getenv("TTS_VOICE", "longfei")
DEFAULT_TTS_RATE = "+5%"    # 语速略微加快更显青年李白的意气风发
DEFAULT_TTS_PITCH = "+2Hz"   # 音调清脆

# 离线教学容灾模式 (当没有配置 API Key 或网络中断时自动开启，使用高质量内置知识库与预置音频)
OFFLINE_DEMO_MODE = os.getenv("OFFLINE_DEMO_MODE", "true").lower() == "true"
