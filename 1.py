import streamlit as st

st.set_page_config(page_title="单词复习助手", page_icon="📘", layout="centered")

# ===== 标题与进度 =====
st.title("📚 单词复习小助手")
st.markdown("### 第 1 / 1000 个单词")

# ===== 内容区 =====
st.markdown("**释义：** 优越，优势")
st.markdown("**例句（中文）：** 他在比赛中表现出明显的优势。")

# ===== 输入区 =====
user_input = st.text_input("请输入英文单词：", key="input")
st.button("检查")
st.button("显示英文句子")

# ===== 收藏按钮 =====
col1, col2 = st.columns(2)
with col1:
    st.button("⭐ 收藏")
with col2:
    st.button("🗑 取消收藏")

# ===== 状态显示 =====
st.markdown("✅ **已收藏**")

# ===== 下一个按钮 =====
st.markdown("---")
st.button("下一个 ➡️", use_container_width=True)

# ===== 底部提示 =====
st.markdown("<center>© 2025 你的名字 | Streamlit English Review App</center>", unsafe_allow_html=True)
