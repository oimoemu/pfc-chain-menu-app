
import streamlit as st
import pandas as pd

st.set_page_config(page_title="PFCチェーン店メニュー検索", layout="wide")

st.title("🍽️ チェーン店メニュー PFC 検索アプリ")
st.markdown("各チェーン店のメニューを **たんぱく質・脂質・炭水化物(PFC)** ごとに並べ替えたり、減量・増量に合ったメニューを探せます。")

# CSVファイル読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("menu_data_all_chains.csv")
    return df

df = load_data()

# 店舗選択
store_list = df["店舗名"].dropna().unique().tolist()
selected_store = st.selectbox("📍 店舗を選択してください", store_list)

# 店舗でフィルター
filtered_df = df[df["店舗名"] == selected_store].copy()

# 並べ替え基準選択
sort_column = st.selectbox("🔍 並べ替え基準", ["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"])
sort_order = st.radio("⬆️ 並び順", ["昇順（少ない順）", "降順（多い順）"]) == "降順（多い順）"

# 並べ替え
filtered_df = filtered_df.sort_values(by=sort_column, ascending=not sort_order)

# 結果表示
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
