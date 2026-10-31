"""Local Piper speech synthesis and OpenPronounce pronunciation assessment."""

from __future__ import annotations

import io
import os
import re
import threading
import wave
from functools import lru_cache

VOICES = {
    "美式 · 女声": "en_US-amy-medium",
    "美式 · 男声": "en_US-ryan-medium",
    "英式 · 女声": "en_GB-cori-medium",
    "英式 · 男声": "en_GB-alan-medium",
}
MAX_TEXT_LENGTH = 5000


class SpeechError(Exception):
    """An actionable speech generation or assessment error."""


def validate_text(text: str) -> str:
    """Normalize and validate the reference text."""
    text = text.strip()
    if not text:
        raise SpeechError("请先输入英文内容。")
    if len(text) > MAX_TEXT_LENGTH:
        raise SpeechError(f"文本不能超过 {MAX_TEXT_LENGTH} 个字符。")
    if not re.search(r"[a-zA-Z]", text):
        raise SpeechError("请输入包含英文字母的内容。")
    return text


@lru_cache(maxsize=4)
def _load_voice(voice: str):
    """Load a Piper voice; Hugging Face caches its model files after first use."""
    from huggingface_hub import hf_hub_download
    from piper import PiperVoice

    language, name, quality = voice.split("-", 2)
    folder = f"en/{language}/{name}/{quality}"
    model = hf_hub_download("rhasspy/piper-voices", f"{folder}/{voice}.onnx")
    config = hf_hub_download("rhasspy/piper-voices", f"{folder}/{voice}.onnx.json")
    return PiperVoice.load(model, config)


def synthesize(text: str, voice: str, speed: float) -> bytes:
    """Generate a mono PCM WAV with a locally running Piper voice."""
    text = validate_text(text)
    if voice not in VOICES or speed not in (0.8, 1.0, 1.2):
        raise SpeechError("请选择有效的声音和语速。")
    try:
        from piper.config import SynthesisConfig

        engine = _load_voice(VOICES[voice])
        chunks = engine.synthesize(text, syn_config=SynthesisConfig(length_scale=1 / speed))
        output = io.BytesIO()
        with wave.open(output, "wb") as result:
            result.setnchannels(1)
            result.setsampwidth(2)
            result.setframerate(engine.config.sample_rate)
            for chunk in chunks:
                result.writeframes(chunk.audio_int16_bytes)
        data = output.getvalue()
        if len(data) <= 44:
            raise SpeechError("没有生成音频，请尝试其他英文内容。")
        return data
    except ImportError as exc:
        raise SpeechError("缺少开源语音依赖，请按照说明文件安装。") from exc
    except SpeechError:
        raise
    except Exception as exc:
        raise SpeechError("语音模型加载或生成失败，请检查网络、磁盘空间及模型是否完整。") from exc


_translation_lock = threading.Lock()


def translate_to_chinese(text: str) -> str:
    """Translate English locally with Argos, downloading the language model once."""
    text = validate_text(text)
    try:
        # Avoid the Stanza backend refreshing model resources on every process start.
        os.environ.setdefault("ARGOS_CHUNK_TYPE", "MINISBD")
        import argostranslate.package
        import argostranslate.translate

        with _translation_lock:
            installed = argostranslate.package.get_installed_packages()
            if not any(item.from_code == "en" and item.to_code == "zh" for item in installed):
                argostranslate.package.update_package_index()
                package = next(
                    (
                        item
                        for item in argostranslate.package.get_available_packages()
                        if item.from_code == "en" and item.to_code == "zh"
                    ),
                    None,
                )
                if package is None:
                    raise SpeechError("未找到英译中模型，请稍后重试。")
                argostranslate.package.install_from_path(package.download())
            result = argostranslate.translate.translate(text, "en", "zh")
        if not result or not result.strip():
            raise SpeechError("翻译结果为空，请尝试其他英文内容。")
        return result
    except ImportError as exc:
        raise SpeechError("缺少本地翻译依赖，请按工具说明安装。") from exc
    except SpeechError:
        raise
    except Exception as exc:
        raise SpeechError("本地翻译失败，请检查模型下载、网络连接或磁盘空间后重试。") from exc
