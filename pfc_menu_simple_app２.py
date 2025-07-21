
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="PFCチェーンメニュー", layout="centered")

st.markdown("<h1 style='text-align: center;'>🍱 PFCチェーンメニュー検索</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("menu_data_all_chains.csv")

df = load_data()

# 店舗選択（初期状態で何も選ばれていない）
store_options = ["店舗を選んでください"] + sorted(df["店舗名"].unique().tolist())
store = st.selectbox("店舗を選んでください", store_options)

if store != "店舗を選んでください":
    filtered_df = df[df["店舗名"] == store]

    # メニュー名検索（部分一致）
    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]

    # 並び替え
    sort_by = st.radio("並び替え基準", ["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # 平均PFC表示
    avg = filtered_df[["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].mean()
    st.markdown(
        "### 📈 平均PFC（{} のメニュー）\n- たんぱく質: **{:.1f}g**\n- 脂質: **{:.1f}g**\n- 炭水化物: **{:.1f}g**".format(
            store, avg[0], avg[1], avg[2]
        )
    )

    # 表表示（店舗名を除いて、メニュー名を最初に）
    cols = [col for col in filtered_df.columns if col != "店舗名"]
    st.dataframe(filtered_df[cols].reset_index(drop=True))

else:
    st.info("店舗を選んでください。")
