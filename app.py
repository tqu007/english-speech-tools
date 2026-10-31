"""Standalone English text-to-speech application."""

import streamlit as st

from service import MAX_TEXT_LENGTH, VOICES, SpeechError, synthesize, translate_to_chinese

st.set_page_config(page_title="英语音频生成", page_icon="🎧", layout="wide")
st.title("🎧 英语音频生成")
st.caption("输入英文，生成示范音频或翻译成中文。音频和翻译均在本地处理。")

source_col, translation_col = st.columns(2, gap="large")
with source_col:
    text = st.text_area(
        "英文内容",
        placeholder="例如：Tell me about a time when you solved a difficult problem.",
        height=400,
        max_chars=MAX_TEXT_LENGTH,
    )

with translation_col:
    translation = st.session_state.get("translation")
    translation_current = translation and translation["source"] == text.strip()
    st.text_area(
        "中文翻译",
        value=translation["result"] if translation_current else "",
        placeholder="点击下方按钮，将英文翻译成中文。",
        height=400,
        disabled=True,
    )
    if st.button("翻译成中文", use_container_width=True):
        try:
            with st.spinner("正在本地翻译；首次使用可能需要下载模型…"):
                translated = translate_to_chinese(text)
            st.session_state.translation = {"source": text.strip(), "result": translated}
            st.rerun()
        except SpeechError as exc:
            st.error(str(exc))
    if translation and not translation_current:
        st.caption("英文内容已更改，请重新翻译。")

st.divider()
voice_col, speed_col = st.columns(2)
with voice_col:
    voice = st.selectbox("发音", list(VOICES))
with speed_col:
    speed = st.selectbox("语速", [0.8, 1.0, 1.2], index=1, format_func=lambda value: f"{value:g}×")

if st.button("生成音频", type="primary", use_container_width=True):
    try:
        with st.spinner("正在本地生成音频，首次使用该声音需要下载模型…"):
            audio = synthesize(text, voice, speed)
        st.session_state.sample = {"audio": audio, "settings": ("piper", text.strip(), voice, speed)}
    except SpeechError as exc:
        st.error(str(exc))

sample = st.session_state.get("sample")
if sample and sample["settings"] == ("piper", text.strip(), voice, speed):
    st.audio(sample["audio"], format="audio/wav")
    st.download_button("下载 WAV", sample["audio"], file_name="english_practice.wav", mime="audio/wav")
elif sample:
    st.info("文本或设置已更改，请重新生成音频。")
