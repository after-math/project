import streamlit as st
import pandas as pd
import os

# ==================== 文件路径 ====================
WORDS_FILE = "sentences.csv"
LEARNED_FILE = "learned.txt"
FAVORITES_FILE = "favorites.txt"

# ==================== 初始化 ====================
st.set_page_config(page_title="智能英语默写系统——程嘉明", page_icon="📘", layout="centered")

# ===== 检查是否存在单词文件 =====
if not os.path.exists(WORDS_FILE):
    st.error("❌ 未找到 sentences.csv，请上传文件。")
    uploaded = st.file_uploader("上传 sentences.csv 文件", type="csv")
    if uploaded:
        with open(WORDS_FILE, "wb") as f:
            f.write(uploaded.read())
        st.success("✅ 文件上传成功，请重新运行程序。")
    st.stop()

words = pd.read_csv(WORDS_FILE, header=None, names=["word", "meaning", "sentence", "translation"])

# ==================== 状态变量 ====================
if "learned" not in st.session_state:
    st.session_state.learned = set()
    if os.path.exists(LEARNED_FILE):
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                st.session_state.learned.add(line.strip().lower())

if "favorites" not in st.session_state:
    st.session_state.favorites = set()
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().split(",")[0].lower()
                if w:
                    st.session_state.favorites.add(w)

if "index" not in st.session_state:
    st.session_state.index = 0

# 👉 新增：访问历史栈，用于“上一个”
if "history" not in st.session_state:
    st.session_state.history = []

# 👉 新增：初始化时把 index 放到第一个“未掌握”的单词（只做一次）
if "initialized" not in st.session_state:
    i = st.session_state.index
    while i < len(words) and str(words.iloc[i, 0]).lower() in st.session_state.learned:
        i += 1
    st.session_state.index = min(i, len(words) - 1)
    st.session_state.initialized = True

# ==================== 结束状态 ====================
if st.session_state.index >= len(words):
    st.success("🎉 恭喜！你已掌握所有单词！")
    st.stop()

# 当前单词
current = words.iloc[st.session_state.index]
word = str(current["word"])
meaning = str(current["meaning"])
sentence = str(current["sentence"])
translation = str(current["translation"])

# ==================== 居中标题 ====================
st.markdown("<h1 style='text-align:center;'>📘 智能英语默写系统</h1>", unsafe_allow_html=True)
st.subheader(f"进度：{st.session_state.index + 1} / {len(words)}")

# ==================== 中文释义 + 中文例句 ====================
st.markdown(
    f"""
    ### 📖 中文释义: {meaning}
    <hr style='border: 2px solid #B22222; border-radius: 5px; margin-top: -10px; margin-bottom: 5px;'>
    <div style='font-size:18px; color:#CCCCCC; margin-bottom:15px;'>
        💬 <b>中文例句：</b>{translation}
    </div>
    """,
    unsafe_allow_html=True
)

# ==================== 英语输入 ====================
st.markdown("✏️ 请写出对应的英文单词：")
st.text_input("", key="user_input", label_visibility="collapsed")

# ======= 辅助：找到下一个未掌握的索引 =======
def find_next_unlearned(start_idx: int) -> int:
    i = start_idx + 1
    while i < len(words) and str(words.iloc[i, 0]).lower() in st.session_state.learned:
        i += 1
    return i  # 可能返回 len(words)

# ==================== 操作按钮 ====================
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("✅ 检查答案", use_container_width=True):
        user_input = st.session_state.user_input.strip().lower()
        if user_input == word.lower():
            st.success(f"✅ 正确！{word}")
            # 记录学习
            st.session_state.learned.add(word.lower())
            with open(LEARNED_FILE, "a", encoding="utf-8") as f:
                f.write(word + "\n")
            # 记录历史（便于回退到当前这个）
            st.session_state.history.append(st.session_state.index)
            # 跳到下一个未掌握
            nxt = find_next_unlearned(st.session_state.index)
            if nxt < len(words):
                st.session_state.index = nxt
                st.rerun()
            else:
                st.success("🎉 所有单词已掌握！")
        else:
            st.error(f"❌ 错误，应为：{word}")

with col2:
    if st.button("➡️ 下一个", use_container_width=True):
        # 前进前记录历史
        st.session_state.history.append(st.session_state.index)
        # 跳到下一个（跳过已掌握）
        nxt = find_next_unlearned(st.session_state.index)
        if nxt < len(words):
            st.session_state.index = nxt
            st.rerun()
        else:
            st.info("🎉 已经是最后一个未掌握的单词！")

with col3:
    if st.button("⬅️ 上一个", use_container_width=True):
        if st.session_state.history:
            st.session_state.index = st.session_state.history.pop()
            st.rerun()
        else:
            st.warning("🚫 没有更早的历史记录。")

# ==================== 收藏 & 显示英文例句 并排 ====================
st.divider()
fav_col, sen_col = st.columns([1, 1])

with fav_col:
    if word.lower() in st.session_state.favorites:
        st.markdown("⭐ 当前单词已收藏")
        if st.button("🗑 取消收藏", use_container_width=True):
            st.session_state.favorites.remove(word.lower())
            # 重写 favorites.txt
            if os.path.exists(FAVORITES_FILE):
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                    for line in lines:
                        if not line.lower().startswith(word.lower() + ","):
                            f.write(line)
            st.success(f"已取消收藏 {word}")
    else:
        if st.button("⭐ 收藏当前单词", use_container_width=True):
            with open(FAVORITES_FILE, "a", encoding="utf-8") as f:
                f.write(f"{word},{meaning},{sentence},{translation}\n")
            st.session_state.favorites.add(word.lower())
            st.success(f"已收藏 {word}")

with sen_col:
    if st.button("📜 显示英文例句", use_container_width=True):
        st.info(f"**{sentence}**")
