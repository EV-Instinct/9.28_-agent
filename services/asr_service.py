"""
百炼 Paraformer 语音识别服务（朗读测评专用）

把学生麦克风录音转成文字，交给 reader_evaluator 做序列比对打分。

设计要点：
- Paraformer 要求 16kHz 单声道 WAV，这里统一规整后再送识别；
- 优先用标准库 wave 处理（无外部依赖），异常时回退 ffmpeg；
- API Key 复用 .env 中的 DashScope Key，无需额外配置。
"""
import io
import os
import time
import wave
import array
import glob
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from http import HTTPStatus

import dashscope
from dashscope.audio.asr import Recognition

from config import DEFAULT_API_KEY, AUDIO_DIR

TARGET_RATE = 16000
ASR_MODEL = "paraformer-realtime-v2"

# ffmpeg 定位缓存（None=未探测，""=探测过但没找到）
_FFMPEG_CACHE: Optional[str] = None


def _find_ffmpeg() -> Optional[str]:
    """定位 ffmpeg 可执行文件。

    浏览器 st.audio_input 上传的是 webm/opus 容器（不是 WAV），必须经 ffmpeg
    转码，因此这里要尽最大努力找到它，避免"识别为空"这种静默失败。
    查找顺序：环境变量 FFMPEG_BINARY > PATH > Windows 常见安装位置。
    """
    global _FFMPEG_CACHE
    if _FFMPEG_CACHE is not None:
        return _FFMPEG_CACHE or None

    cand = os.getenv("FFMPEG_BINARY") or shutil.which("ffmpeg")
    if not cand:
        patterns = [
            # WinGet 安装的 Gyan.FFmpeg（本机实际位置）
            r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\ffmpeg.exe",
            r"C:\Users\*\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        ]
        for pat in patterns:
            hits = glob.glob(pat, recursive=True)
            if hits:
                cand = hits[0]
                break

    _FFMPEG_CACHE = cand or ""
    return cand or None


class ASRService:
    def __init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or DEFAULT_API_KEY
        self.tmp_dir = Path(AUDIO_DIR)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    # ---------------- 音频规整 ----------------
    @staticmethod
    def _normalize_wav(raw: bytes) -> Optional[bytes]:
        """把 WAV 字节流规整为 16kHz / 单声道 / 16bit（纯标准库实现）"""
        try:
            with wave.open(io.BytesIO(raw), "rb") as wf:
                channels = wf.getnchannels()
                width = wf.getsampwidth()
                rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
        except Exception:
            return None

        if width != 2 or not frames:
            return None

        samples = array.array("h")
        samples.frombytes(frames)

        # 立体声 -> 单声道
        if channels == 2:
            samples = array.array(
                "h", [(samples[i] + samples[i + 1]) // 2
                      for i in range(0, len(samples) - 1, 2)]
            )

        # 重采样到 16kHz（线性插值，语音识别足够）
        if rate and rate != TARGET_RATE:
            ratio = rate / TARGET_RATE
            out_len = max(int(len(samples) / ratio), 1)
            samples = array.array(
                "h", [samples[min(int(i * ratio), len(samples) - 1)]
                      for i in range(out_len)]
            )

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(TARGET_RATE)
            wf.writeframes(samples.tobytes())
        return buf.getvalue()

    @staticmethod
    def _ffmpeg_normalize(raw: bytes) -> Optional[bytes]:
        """用 ffmpeg 转 16k 单声道 wav。

        这是**真实浏览器录音的主路径**：st.audio_input 上传的是 webm/opus，
        纯标准库无法解码，只能交给 ffmpeg。
        """
        ffmpeg = _find_ffmpeg()
        if not ffmpeg:
            print("[ASR] 未找到 ffmpeg：浏览器录音为 webm 容器，无法转码。"
                  "请安装 ffmpeg 或设置环境变量 FFMPEG_BINARY。")
            return None

        src = dst = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fin:
                fin.write(raw)
                src = fin.name
            dst = src + ".16k.wav"
            proc = subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", src,
                 "-ar", str(TARGET_RATE), "-ac", "1", "-f", "wav", dst],
                capture_output=True, timeout=60,
            )
            if proc.returncode != 0:
                print(f"[ASR] ffmpeg 转码失败({proc.returncode}): "
                      f"{proc.stderr.decode('utf-8', 'ignore')[:200]}")
                return None
            with open(dst, "rb") as f:
                return f.read()
        except subprocess.TimeoutExpired:
            print("[ASR] ffmpeg 转码超时(60s)")
            return None
        except Exception as e:
            print(f"[ASR] ffmpeg 转码异常 {type(e).__name__}: {e}")
            return None
        finally:
            for p in (src, dst):
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    # ---------------- 对外接口 ----------------
    def transcribe_bytes(self, raw: bytes) -> str:
        """识别音频字节流，返回识别文本；失败返回空串（调用方需处理）"""
        if not raw:
            return ""

        # 用魔数快速分流：浏览器 st.audio_input 上传的是 WebM(EBML, 1A45DFA3)；
        # WAV 则走纯标准库的轻量路径，避免无谓的 ffmpeg 开销。
        if raw[:4] == b"RIFF":
            wav = self._normalize_wav(raw)
            if wav is None:
                wav = self._ffmpeg_normalize(raw)
        else:
            wav = self._ffmpeg_normalize(raw)

        if not wav:
            print(f"[ASR] 音频规整失败：魔数 {raw[:4].hex()}，"
                  f"{len(raw)} bytes，ffmpeg 亦无法转换")
            return ""

        path = self.tmp_dir / f"read_{int(time.time() * 1000)}.wav"
        try:
            path.write_bytes(wav)
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY") or self.api_key or DEFAULT_API_KEY
            recognition = Recognition(
                model=ASR_MODEL,
                format="wav",
                sample_rate=TARGET_RATE,
                language_hints=["zh"],
                callback=None,
            )
            result = recognition.call(str(path))
            if result.status_code != HTTPStatus.OK:
                print(f"[ASR Error] {result.status_code} {result.message}")
                return ""
            sentences = result.get_sentence()
            if isinstance(sentences, list):
                return "".join(s.get("text", "") for s in sentences)
            return sentences.get("text", "")
        except Exception as e:
            print(f"[ASR Exception] {type(e).__name__}: {e}")
            return ""
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    def is_available(self) -> bool:
        """是否具备云端识别条件（有 Key 且未禁用）"""
        return bool(self.api_key and self.api_key.strip())


asr_service = ASRService()
