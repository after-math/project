import streamlit as st
import pandas as pd
import pymysql

# ==================== 页面配置 ====================
st.set_page_config(page_title="智能英语默写系统——程嘉明", page_icon="📘", layout="centered")
st.image("微信图片_20251019001113_188.jpg", caption="智能英语默写系统", use_column_width=True)

# ==================== 数据库连接 ====================
def get_conn():
    # 每次调用创建新连接，防止缓存冲突或回滚失败
    return pymysql.connect(
        host="rm-wz97z0ykk16h460i9to.mysql.rds.aliyuncs.com",
        user="streamlit",
        password="Cjm20040224",
        database="word",
        charset="utf8mb4",
        autocommit=True
    )

# ==================== 批次加载配置 ====================
BATCH_SIZE = 200

if "batch" not in st.session_state:
    st.session_state.batch = 0
if "index" not in st.session_state:
    st.session_state.index = 0
if "learned" not in st.session_state:
    st.session_state.learned = set()
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "history" not in st.session_state:
    st.session_state.history = []

# ==================== 分批加载函数 ====================
@st.cache_data(show_spinner=False)
def load_words_batch(batch_index: int):
    """分页加载一批单词"""
    offset = batch_index * BATCH_SIZE
    sql = f"""
        SELECT word, meaning, sentence, translation
        FROM words
        ORDER BY word ASC
        LIMIT {BATCH_SIZE} OFFSET {offset}
    """
    conn = get_conn()
    try:
        df = pd.read_sql(sql, conn)
    finally:
        conn.close()
    return df

# 加载当前批次单词
words = load_words_batch(st.session_state.batch)

# 尝试预加载下一批（若失败则忽略）
try:
    _ = load_words_batch(st.session_state.batch + 1)
except Exception:
    pass

# ==================== 加载学习与收藏状态 ====================
@st.cache_data(ttl=60)
def load_status():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT word FROM learned")
            learned = {r[0].lower() for r in cur.fetchall()}
            cur.execute("SELECT word FROM favorites")
            favorites = {r[0].lower() for r in cur.fetchall()}
    finally:
        conn.close()
    return learned, favorites

st.session_state.learned, st.session_state.favorites = load_status()

# ==================== 判断是否学完当前批次 ====================
if st.session_state.index >= len(words):
    st.session_state.batch += 1
    st.session_state.index = 0
    words = load_words_batch(st.session_state.batch)
    if words.empty:
        st.success("🎉 所有单词都已掌握！")
        st.stop()

# ==================== 当前单词 ====================
current = words.iloc[st.session_state.index]
word = str(current["word"])
meaning = str(current["meaning"])
sentence = str(current["sentence"])
translation = str(current["translation"])

# ==================== 页面标题 ====================
st.markdown("<h1 style='text-align:center;'>📘 智能英语默写系统</h1>", unsafe_allow_html=True)
st.subheader(f"📚 第 {st.session_state.batch + 1} 批 · 进度：{st.session_state.index + 1} / {len(words)}")

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

# ==================== 数据库操作函数 ====================
def add_learned(word):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT IGNORE INTO learned (word) VALUES (%s)", (word,))
    finally:
        conn.close()

def add_favorite(word, meaning, sentence, translation):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO favorites (word, meaning, sentence, translation) VALUES (%s, %s, %s, %s)",
                (word, meaning, sentence, translation)
            )
    finally:
        conn.close()

def remove_favorite(word):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE word=%s", (word,))
    finally:
        conn.close()

# ==================== 辅助函数 ====================
def find_next_unlearned(start_idx: int) -> int:
    i = start_idx + 1
    while i < len(words) and str(words.iloc[i, 0]).lower() in st.session_state.learned:
        i += 1
    return i

# ==================== 表单交互 ====================
with st.form("answer_form"):
    user_input = st.text_input("✏️ 请写出对应的英文单词：", key="user_input", label_visibility="collapsed")

    col1, col2, col3 = st.columns([1, 1, 1])
    submitted = col1.form_submit_button("✅ 检查答案")
    next_btn = col2.form_submit_button("➡️ 下一个")
    prev_btn = col3.form_submit_button("⬅️ 上一个")

    if submitted:
        u = user_input.strip().lower()
        if u == word.lower():
            st.success(f"✅ 正确！{word}")
            add_learned(word)
            st.session_state.learned.add(word.lower())
            st.session_state.history.append(st.session_state.index)
            nxt = find_next_unlearned(st.session_state.index)
            if nxt < len(words):
                st.session_state.index = nxt
                st.rerun()
            else:
                st.session_state.index = len(words)
                st.rerun()
        else:
            st.error(f"❌ 错误，应为：{word}")

    elif next_btn:
        st.session_state.history.append(st.session_state.index)
        nxt = find_next_unlearned(st.session_state.index)
        if nxt < len(words):
            st.session_state.index = nxt
            st.rerun()
        else:
            st.session_state.index = len(words)
            st.rerun()

    elif prev_btn:
        if st.session_state.history:
            st.session_state.index = st.session_state.history.pop()
            st.rerun()
        else:
            st.warning("🚫 没有更早的历史记录。")

# ==================== 收藏 & 显示英文例句 ====================
st.divider()
col_fav, col_sen = st.columns([1, 1])

with col_fav:
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

with col_sen:
    if st.button("📜 显示英文例句", use_container_width=True):
        st.info(f"**{sentence}**")
