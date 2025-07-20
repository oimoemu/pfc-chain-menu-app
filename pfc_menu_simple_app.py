
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="PFCチェーンメニュー", layout="centered")

st.markdown("<h1 style='text-align: center;'>🍱 PFCチェーンメニュー検索</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("menu_data_all_chains.csv")

df = load_data()

# 店舗選択
store = st.selectbox("店舗を選んでください", sorted(df["店舗名"].unique()))

# メニュー名検索（部分一致）
keyword = st.text_input("メニュー名で絞り込み（例：チーズ）")
filtered_df = df[df["店舗名"] == store]
if keyword:
    filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]

# 並び替え
sort_by = st.radio("並び替え基準", ["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
filtered_df = filtered_df.sort_values(by=sort_by)

# 表示
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

# チェックボックスで選択し、合計表示
st.markdown("### ✅ メニューを選んで合計PFCを表示")
selected = st.multiselect("メニュー選択", filtered_df["メニュー名"])
if selected:
    total = filtered_df[filtered_df["メニュー名"].isin(selected)][["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
    st.write("合計PFC：")
    st.write(f"たんぱく質：{total[0]:.1f}g / 脂質：{total[1]:.1f}g / 炭水化物：{total[2]:.1f}g")

    # レーダーチャート
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[total[0], total[1], total[2]],
        theta=["たんぱく質", "脂質", "炭水化物"],
        fill='toself',
        name='合計PFC'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("📲 スマホで使うときは「ホーム画面に追加」でアプリのように使えます")
