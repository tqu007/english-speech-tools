"""Tests for offline speech and translation."""

import io
import sys
import types
import wave
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import service


def test_input_validation():
    assert service.validate_text(" Hello ") == "Hello"
    with pytest.raises(service.SpeechError):
        service.validate_text("  ")
    with pytest.raises(service.SpeechError):
        service.synthesize("Hello", "unknown", 1.0)


def test_synthesis_uses_voice_and_speed(monkeypatch):
    seen = {}

    class Config:
        def __init__(self, length_scale):
            self.length_scale = length_scale

    class Voice:
        config = types.SimpleNamespace(sample_rate=22050)

        def synthesize(self, text, syn_config):
            seen.update(text=text, length_scale=syn_config.length_scale)
            return [types.SimpleNamespace(audio_int16_bytes=b"\x01\x00" * 200)]

    def load_voice(voice):
        seen["voice"] = voice
        return Voice()

    monkeypatch.setitem(sys.modules, "piper", types.ModuleType("piper"))
    monkeypatch.setitem(sys.modules, "piper.config", types.SimpleNamespace(SynthesisConfig=Config))
    monkeypatch.setattr(service, "_load_voice", load_voice)
    result = service.synthesize("Hello", "英式 · 男声", 0.8)
    assert seen == {"voice": "en_GB-alan-medium", "text": "Hello", "length_scale": 1.25}
    with wave.open(io.BytesIO(result)) as audio:
        assert audio.getframerate() == 22050
        assert audio.getnframes() == 200


def test_translation_installed_model(monkeypatch):
    package = types.ModuleType("argostranslate.package")
    package.get_installed_packages = lambda: [types.SimpleNamespace(from_code="en", to_code="zh")]
    translate = types.ModuleType("argostranslate.translate")
    translate.translate = lambda text, source, target: "你好"
    argos = types.ModuleType("argostranslate")
    argos.__path__ = []
    argos.package = package
    argos.translate = translate
    monkeypatch.setitem(sys.modules, "argostranslate", argos)
    monkeypatch.setitem(sys.modules, "argostranslate.package", package)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", translate)
    assert service.translate_to_chinese("Hello") == "你好"
