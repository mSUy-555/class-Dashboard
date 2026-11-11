import os
import sqlite3
import streamlit as st
import pandas as pd

# ---------- 数据库配置 ----------
# 锚定到脚本目录，避免不同 cwd 下出现多份 sqlite 文件
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "class_db.sqlite")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    student_id TEXT    NOT NULL,
    score      REAL    NOT NULL,
    created_at TEXT    DEFAULT CURRENT_TIMESTAMP
);
"""

def get_connection() -> sqlite3.Connection:
    # check_same_thread=False 是 Streamlit 多线程场景下的常规做法
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_table():
    """启动时确保 students 表存在，已存在则跳过。"""
    conn = get_connection()
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()

def insert_student(name: str, student_id: str, score: float):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students (name, student_id, score) VALUES (?, ?, ?)",
            (name, student_id, score),
        )
        conn.commit()
    finally:
        conn.close()

def load_students_df() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT name, student_id, score FROM students ORDER BY id", conn
        )
    finally:
        conn.close()
    return df

# ---------- 页面 ----------
st.set_page_config(page_title="学生成绩管理", layout="wide")
st.title("📘 学生成绩管理系统")

# 启动时自动建表（幂等）
ensure_table()

col_form, col_view = st.columns([1, 2])

with col_form:
    st.subheader("✏️ 录入学生")
    with st.form("student_form"):
        name = st.text_input("姓名")
        student_id = st.text_input("学号")
        score = st.number_input("成绩", min_value=0.0, max_value=100.0, step=0.5)
        submitted = st.form_submit_button("提交入库")

    if submitted:
        if not name.strip() or not student_id.strip():
            st.warning("姓名和学号不能为空")
        else:
            try:
                insert_student(name.strip(), student_id.strip(), float(score))
                st.success(f"已录入：{name}（{student_id}）→ {score}")
            except Exception as e:
                st.error(f"入库失败：{e}")

with col_view:
    st.subheader("📋 学生列表")
    try:
        df = load_students_df()
    except Exception as e:
        st.error(f"读取数据失败：{e}")
        df = pd.DataFrame(columns=["name", "student_id", "score"])

    if df.empty:
        st.info("暂无数据，左侧录入后即可看到。")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("📊 成绩柱状图")
        chart_df = df.set_index("name")[["score"]]
        st.bar_chart(chart_df, use_container_width=True)
