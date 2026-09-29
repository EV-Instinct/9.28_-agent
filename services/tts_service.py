"""
多引擎语音合成服务 (优先阿里百炼 CosyVoice 大模型语音，支持 Edge-TTS 双轨容灾)
支持动态切换李白专属男声音色，带音色隔离的 MD5 极速缓存。
"""
import os
import hashlib
import asyncio
from pathlib import Path
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
import edge_tts
from config import AUDIO_DIR, DEFAULT_TTS_VOICE, DEFAULT_TTS_RATE, DEFAULT_TTS_PITCH, DEFAULT_API_KEY

DASHSCOPE_VOICES = {
    "longfei": "cosyvoice-v1",   # 激情豪迈男声（诗词朗诵专长，极度契合李白）
    "longcheng": "cosyvoice-v1", # 阳光洒脱男声（少年李白意气风发）
    "longshuo": "cosyvoice-v1",  # 沉稳英挺男声（名家诗仙风骨）
    "longze": "cosyvoice-v1"     # 温润清朗男声（活力明朗少年）
}

class TTSService:
    def __init__(self, voice: str = DEFAULT_TTS_VOICE, rate: str = DEFAULT_TTS_RATE, pitch: str = DEFAULT_TTS_PITCH):
        self.voice = voice or "longfei"
        self.rate = rate
        self.pitch = pitch

    def set_voice(self, new_voice: str):
        """动态切换音色（确保设置即生效）"""
        if new_voice and str(new_voice).strip():
            self.voice = str(new_voice).strip()

    def _get_cache_path(self, text: str, voice: str = None) -> Path:
        """根据文本和音色参数生成哈希缓存文件名（带音色隔离，切换音色绝不串音）"""
        v = voice or self.voice
        clean_text = text.strip()
        hash_str = f"dash_{v}_{clean_text}"
        md5_hash = hashlib.md5(hash_str.encode("utf-8")).hexdigest()
        return AUDIO_DIR / f"libai_{v}_{md5_hash}.mp3"

    def _synthesize_dashscope(self, text: str, voice: str, output_path: Path) -> bool:
        """调用阿里百炼 CosyVoice 合成高品质情感人声"""
        api_key = os.getenv("DASHSCOPE_API_KEY") or DEFAULT_API_KEY
        if not api_key:
            return False
        dashscope.api_key = api_key
        try:
            model = DASHSCOPE_VOICES.get(voice, "cosyvoice-v1")
            syn = SpeechSynthesizer(model=model, voice=voice)
            audio_bytes = syn.call(text)
            if audio_bytes and len(audio_bytes) > 500:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                return True
        except Exception as e:
            print(f"[DashScope CosyVoice Error]: {e}")
        return False

    async def _synthesize_edge_async(self, text: str, voice: str, output_path: Path) -> bool:
        """备选调用 edge-tts 异步合成音频"""
        try:
            edge_v = voice if "Neural" in voice else "zh-CN-YunyangNeural"
            communicate = edge_tts.Communicate(
                text=text,
                voice=edge_v,
                rate=self.rate,
                pitch=self.pitch
            )
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            print(f"[Edge-TTS Error]: {e}")
            return False

    def generate_speech(self, text: str, voice_override: str = None) -> str:
        """
        核心生成入口：
        若当前音色为百炼音色，优先调用阿里百炼 CosyVoice 大模型语音；
        若无网或调用失败，自动降级至 Edge-TTS。
        """
        if not text or not text.strip():
            return ""

        current_voice = voice_override or self.voice
        output_path = self._get_cache_path(text, current_voice)
        if output_path.exists() and output_path.stat().st_size > 0:
            return str(output_path)

        # 1. 优先尝试阿里百炼 CosyVoice 云端大模型语音
        if current_voice in DASHSCOPE_VOICES or "Neural" not in current_voice:
            dash_voice = current_voice if current_voice in DASHSCOPE_VOICES else "longfei"
            success = self._synthesize_dashscope(text, dash_voice, output_path)
            if success and output_path.exists():
                return str(output_path)

        # 2. 降级尝试 Edge-TTS
        try:
            edge_voice = current_voice if "Neural" in current_voice else "zh-CN-YunyangNeural"
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                success = loop.run_until_complete(self._synthesize_edge_async(text, edge_voice, output_path))
            else:
                success = asyncio.run(self._synthesize_edge_async(text, edge_voice, output_path))
            if success and output_path.exists():
                return str(output_path)
        except Exception as e:
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                success = new_loop.run_until_complete(self._synthesize_edge_async(text, edge_voice, output_path))
                new_loop.close()
                if success and output_path.exists():
                    return str(output_path)
            except Exception as inner_e:
                print(f"[TTS Fallback Error]: {inner_e}")

        return ""

# 单例导出
tts_service = TTSService()
