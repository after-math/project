import streamlit as st
from gtts import gTTS
import io

# ================= 页面设置 =================
st.set_page_config(page_title="英语朗读示例", page_icon="🎧", layout="centered")

st.title("🎧 英文语音朗读示例（gTTS 版本）")
st.markdown("💡 该版本完全兼容 Streamlit Cloud，可直接部署，无需异步。")

# ================= 输入内容 =================
text = st.text_area("✏️ 输入要朗读的英文：", "Success is not final, failure is not fatal; it is the courage to continue that counts.")

# ================= 播放语音 =================
if st.button("🔊 播放英文语音"):
    if not text.strip():
        st.warning("请输入英文内容。")
    else:
        # 使用 Google TTS 合成语音
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # 播放音频
        st.audio(mp3_fp, format="audio/mp3")
        st.success("✅ 播放成功！Enjoy~ 🎵")

# ================= 页脚 =================
st.divider()
st.caption("📘 Powered by Google Text-to-Speech (gTTS) · 适合部署在 Streamlit Cloud 环境")
