import streamlit as st
import pandas as pd
import pymysql
import os
from gtts import gTTS
import io
import base64

# ==================== 页面配置 ====================
st.set_page_config(page_title="智能英语默写系统——程嘉明", page_icon="📘", layout="centered")

# ==================== 数据库连接 ====================
def get_conn():
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
for key, value in {
    "batch": 0, "index": 0, "learned": set(),
    "favorites": set(), "history": [], "clear_input": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==================== 分批加载函数 ====================
@st.cache_data(show_spinner=False)
def load_words_batch(batch_index: int):
    offset = batch_index * BATCH_SIZE
    sql = f"""
        SELECT id, word, meaning, sentence, translation
        FROM words
        ORDER BY id ASC
        LIMIT {BATCH_SIZE} OFFSET {offset}
    """
    conn = get_conn()
    try:
        df = pd.read_sql(sql, conn)
    finally:
        conn.close()
    return df

words = load_words_batch(st.session_state.batch)

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

# ==================== 自动跳过已学单词 ====================
def skip_learned():
    while True:
        words = load_words_batch(st.session_state.batch)
        if st.session_state.index >= len(words):
            st.session_state.batch += 1
            st.session_state.index = 0
            if words.empty:
                st.success("🎉 所有单词都已掌握！")
                st.stop()
        else:
            current_word = str(words.iloc[st.session_state.index]["word"]).lower()
            if current_word in st.session_state.learned:
                st.session_state.index += 1
            else:
                break
    return load_words_batch(st.session_state.batch)

words = skip_learned()

# ==================== 当前单词 ====================
current = words.iloc[st.session_state.index]
word = str(current["word"])
meaning = str(current["meaning"])
sentence = str(current["sentence"])
translation = str(current["translation"])

# ==================== 页面标题 ====================
st.markdown("<h1 style='text-align:center;'>📘 智能英语默写系统——程嘉明</h1>", unsafe_allow_html=True)
st.subheader(f"📚 第 {st.session_state.batch + 1} 批 · 进度：{st.session_state.index + 1} / {len(words)}")

# ==================== 中文释义 + 中文例句 ====================
st.markdown(
    f"""
    ### 📖 中文释义: {meaning}
    ### 💬 例   句: {translation}
    """,
    unsafe_allow_html=True
)

# ==================== 数据库操作函数 ====================
def add_learned(word, meaning, sentence, translation):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO learned (word, meaning, sentence, translation)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    meaning = VALUES(meaning),
                    sentence = VALUES(sentence),
                    translation = VALUES(translation)
                """,
                (word, meaning, sentence, translation)
            )
        exists = False
        if os.path.exists("learned.txt"):
            with open("learned.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if line.lower().startswith(word.lower() + ","):
                        exists = True
                        break
        if not exists:
            with open("learned.txt", "a", encoding="utf-8") as f:
                f.write(f"{word},{meaning},{sentence},{translation}\n")
    finally:
        conn.close()

def add_favorite(word, meaning, sentence, translation):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO favorites (word, meaning, sentence, translation) VALUES (%s,%s,%s,%s)",
                (word, meaning, sentence, translation)
            )
        with open("favorites.txt", "a", encoding="utf-8") as f:
            f.write(f"{word},{meaning},{sentence},{translation}\n")
    finally:
        conn.close()

def remove_favorite(word):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE word=%s", (word,))
        if os.path.exists("favorites.txt"):
            with open("favorites.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open("favorites.txt", "w", encoding="utf-8") as f:
                for line in lines:
                    if not line.lower().startswith(word.lower() + ","):
                        f.write(line)
    finally:
        conn.close()

def add_progress(word):
    with open("progress.txt", "a", encoding="utf-8") as f:
        f.write(f"{word}\n")

# ==================== 辅助函数 ====================
def find_next_unlearned(start_idx: int) -> int:
    i = start_idx + 1
    while i < len(words) and str(words.iloc[i, 1]).lower() in st.session_state.learned:
        i += 1
    return i

# ==================== 表单交互 ====================
if st.session_state.clear_input:
    st.session_state.user_input = ""
    st.session_state.clear_input = False

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
            add_learned(word, meaning, sentence, translation)
            add_progress(word)
            st.session_state.learned.add(word.lower())
            st.session_state.history.append(st.session_state.index)
            nxt = find_next_unlearned(st.session_state.index)
            st.session_state.index = nxt if nxt < len(words) else len(words)
            st.session_state.clear_input = True
            st.rerun()
        else:
            st.error(f"❌ 错误，应为：{word}")

    elif next_btn:
        st.session_state.history.append(st.session_state.index)
        nxt = find_next_unlearned(st.session_state.index)
        st.session_state.index = nxt if nxt < len(words) else len(words)
        st.session_state.clear_input = True
        st.rerun()

    elif prev_btn:
        if st.session_state.history:
            st.session_state.index = st.session_state.history.pop()
            st.session_state.clear_input = True
            st.rerun()
        else:
            st.warning("🚫 没有更早的历史记录。")

# ==================== 收藏 & 显示英文例句 ====================
st.divider()
col_fav, col_sen, col_play = st.columns([1, 1, 1])

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

# ==================== gTTS 语音播放功能 ====================
with col_play:
    if st.button("🔊 播放英文例句", use_container_width=True):
        if sentence.strip():
            # 使用 gTTS 生成语音
            tts = gTTS(text=sentence, lang='en', slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            # 自动播放
            audio_bytes = mp3_fp.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
                <audio autoplay="true" controls>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            st.success("✅ 正在播放英文例句~")
        else:
            st.warning("⚠️ 当前单词没有英文例句。")
