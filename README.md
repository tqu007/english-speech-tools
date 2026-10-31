# 英语音频与翻译

输入英文，选择美式／英式男女声和 0.8×、1×、1.2× 语速，生成、播放和下载 WAV；也可将英文翻译成中文。使用开源 Piper 和 Argos Translate 本地处理，跟读评分暂不开放。

## 安装与运行

需要 Python 3.11–3.13 和 `uv`。从项目根目录执行：

```bash
uv sync
uv run streamlit run app.py --server.port 8510 --server.address 127.0.0.1
```

访问终端显示的本机地址。

每种声音首次使用时需要联网从 Hugging Face 下载约 60 MB 模型，下载后缓存在本机。缓存齐全后可离线使用，无需 Google 账号、密钥或付费 API。音频和输入文本在本机处理。中文翻译使用开源 Argos Translate，首次翻译需要联网下载英译中模型；安装完成后可离线翻译。

## 技术说明

Streamlit 提供输入、播放和下载界面；`service.py` 使用 [Piper](https://github.com/OHF-Voice/piper1-gpl) 及其声音模型在本地合成单声道 PCM WAV，以模型的长度系数控制语速。四种声音均已在本机实测。当前页面不会录音或调用评分。
