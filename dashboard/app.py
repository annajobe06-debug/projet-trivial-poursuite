"""
Dashboard Streamlit — Benchmark IA sur questions de culture générale.
Lit les résultats depuis gold/benchmark.duckdb (tables mart créées par dbt).
"""
import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Benchmark IA - Trivial Poursuite", layout="wide")

DB_PATH = "gold/benchmark.duckdb"


@st.cache_data
def load_table(table_name: str) -> pd.DataFrame:
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.sql(f"SELECT * FROM {table_name}").df()


st.title("🎯 Benchmark IA — Questions de culture générale")
st.caption("Modèle : gemma2:2b (Ollama) — Dataset : OpenTDB")

# --- Vue globale ---
st.header("Vue d'ensemble")
try:
    df_category = load_table("mart_benchmark_by_category")
    taux_global = (df_category["correct_answers"].sum() / df_category["total_questions"].sum()) * 100
    col1, col2, col3 = st.columns(3)
    col1.metric("Taux de réussite global", f"{taux_global:.1f}%")
    col2.metric("Questions analysées", int(df_category["total_questions"].sum()))
    col3.metric("Catégories couvertes", len(df_category))
except Exception as e:
    st.error(f"Impossible de charger les données : {e}")
    st.stop()

# --- Question 1 : performance par catégorie ---
st.header("1. Performance par catégorie")
st.caption("Dans quelles catégories le modèle est-il le plus performant ?")
st.bar_chart(df_category.set_index("category")["accuracy_percent"])
st.dataframe(df_category, use_container_width=True)

# --- Question 2 : performance par difficulté ---
st.header("2. Performance par difficulté")
st.caption("La difficulté des questions influence-t-elle les performances et le temps de réponse ?")
df_difficulty = load_table("mart_benchmark_by_difficulty")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Taux de réussite (%)")
    st.bar_chart(df_difficulty.set_index("difficulty")["accuracy_percent"])
with col2:
    st.subheader("Temps de réponse moyen (s)")
    st.bar_chart(df_difficulty.set_index("difficulty")["avg_response_time"])

st.dataframe(df_difficulty, use_container_width=True)

# --- Question 3 : performance par type ---
st.header("3. Performance par type de question")
st.caption("Le type de question (Boolean ou Multiple Choice) influence-t-il les performances ?")
df_type = load_table("mart_type_performance")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Taux de réussite (%)")
    st.bar_chart(df_type.set_index("type")["accuracy_percent"])
with col2:
    st.subheader("Temps de réponse moyen (s)")
    st.bar_chart(df_type.set_index("type")["avg_response_time"])

st.dataframe(df_type, use_container_width=True)