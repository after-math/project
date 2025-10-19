import streamlit as st
import pandas as pd
import pymysql

# ==================== 数据库连接函数 ====================
def get_conn():
    return pymysql.connect(
        host="rm-wz97z0ykk16h460i9to.mysql.rds.aliyuncs.com",
        user="streamlit",
        password="Cjm20040224",
        database="word",
        charset="utf8mb4"
    )

# ==================== 页面配置 ====================
st.set_page_config(page_title="智能英语默写系统——程嘉明", page_icon="📘", layout="centered")

# ==================== 顶部图片 ====================
st.image("微信图片_20251019001113_188.jpg", caption="bb", use_column_width=True)

# ==================== 加载 words 表 ====================
@st.cache_data
def load_words():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM words", conn)
    conn.close()
    return df

words = load_words()

# ==================== 初始化状态 ====================
if "index" not in st.session_state:
    st.session_state.index = 0
if "learned" not in st.session_state:
    st.session_state.learned = set()
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "history" not in st.session_state:
    st.session_state.history = []

# ==================== 从数据库读取已学与收藏 ====================
def load_status():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT word FROM learned")
        st.session_state.learned = {r[0].lower() for r in cur.fetchall()}
        cur.execute("SELECT word FROM favorites")
        st.session_state.favorites = {r[0].lower() for r in cur.fetchall()}
    conn.close()

load_status()

# ==================== 当前单词 ====================
if st.session_state.index >= len(words):
    st.success("🎉 恭喜！你已掌握所有单词！")
    st.stop()

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

# ==================== 英语输入框 ====================
st.markdown("✏️ 请写出对应的英文单词：")
st.text_input("", key="user_input", label_visibility="collapsed")

# ==================== 数据库操作函数 ====================
def add_learned(word):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO learned (word) VALUES (%s)", (word,))
    conn.commit()
    conn.close()

def add_favorite(word, meaning, sentence, translation):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO favorites (word, meaning, sentence, translation) VALUES (%s, %s, %s, %s)",
            (word, meaning, sentence, translation),
        )
    conn.commit()
    conn.close()

def remove_favorite(word):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM favorites WHERE word=%s", (word,))
    conn.commit()
    conn.close()

# ==================== 辅助函数 ====================
def find_next_unlearned(start_idx: int) -> int:
    i = start_idx + 1
    while i < len(words) and str(words.iloc[i, 0]).lower() in st.session_state.learned:
        i += 1
    return i

# ==================== 操作按钮 ====================
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("✅ 检查答案", use_container_width=True):
        user_input = st.session_state.user_input.strip().lower()
        if user_input == word.lower():
            st.success(f"✅ 正确！{word}")
            add_learned(word)
            st.session_state.learned.add(word.lower())
            st.session_state.history.append(st.session_state.index)
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
        st.session_state.history.append(st.session_state.index)
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

# ==================== 收藏 & 显示例句 ====================
st.divider()
fav_col, sen_col = st.columns([1, 1])

with fav_col:
    if word.lower() in st.session_state.favorites:
        st.markdown("⭐ 当前单词已收藏")
        if st.button("🗑 取消收藏", use_container_width=True):
            remove_favorite(word)
            st.session_state.favorites.remove(word.lower())
            st.success(f"已取消收藏 {word}")
    else:
        if st.button("⭐ 收藏当前单词", use_container_width=True):
            add_favorite(word, meaning, sentence, translation)
            st.session_state.favorites.add(word.lower())
            st.success(f"已收藏 {word}")

with sen_col:
    if st.button("📜 显示英文例句", use_container_width=True):
        st.info(f"**{sentence}**")
