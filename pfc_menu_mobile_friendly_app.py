
import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go

st.set_page_config(page_title="PFCチェーン店メニュー検索", layout="centered")

st.title("🍱 PFCチェーン店メニュー検索（スマホ対応）")
st.markdown("メニューのPFCを検索・比較・可視化。スマホでも快適に使えます。")

DATA_FILE = "menu_data_all_chains.csv"

@st.cache_data(ttl=60)
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["店舗名", "メニュー名", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"])

df = load_data()

# 店舗名入力と選択
store_input = st.text_input("🔍 店舗名を入力（例: マク）", placeholder="店舗名を入力してください")
matched_stores = df["店舗名"].dropna().unique()
matched_stores = [store for store in matched_stores if store_input.lower() in store.lower()]

if matched_stores:
    selected_store = st.selectbox("🏪 店舗を選択", matched_stores)
    store_df = df[df["店舗名"] == selected_store].copy()

    # メニュー検索
    menu_input = st.text_input("🍔 メニュー名で絞り込み", placeholder="メニュー名を入力（例：チキン）")
    if menu_input:
        store_df = store_df[store_df["メニュー名"].str.contains(menu_input, case=False, na=False)]

    # 数値変換
    for col in ["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]:
        store_df[col] = pd.to_numeric(store_df[col], errors="coerce")

    # フィルター
    goal = st.radio("🎯 フィルター", ["すべて表示", "減量向け", "増量向け"], horizontal=True)
    if goal == "減量向け":
        store_df = store_df[store_df["脂質 (g)"] <= 20]
    elif goal == "増量向け":
        store_df = store_df[(store_df["たんぱく質 (g)"] >= 25) & (store_df["炭水化物 (g)"] >= 60)]

    # 並び替え
    sort_column = st.selectbox("📊 並び替え", ["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"])
    sort_order = st.radio("順序", ["昇順", "降順"], horizontal=True) == "降順"
    store_df = store_df.sort_values(by=sort_column, ascending=not sort_order)

    # メニュー選択
    st.markdown("✅ 合計PFCを見たいメニューを選択")
    selected_rows = st.multiselect("メニュー一覧", store_df["メニュー名"].tolist())
    selected_df = store_df[store_df["メニュー名"].isin(selected_rows)]

    # 表表示
    st.dataframe(store_df.reset_index(drop=True), use_container_width=True)

    if not selected_df.empty:
        total_p = selected_df["たんぱく質 (g)"].sum()
        total_f = selected_df["脂質 (g)"].sum()
        total_c = selected_df["炭水化物 (g)"].sum()

        st.subheader("📦 合計PFC（選択メニュー）")
        st.metric("🥩 たんぱく質", f"{total_p:.1f} g")
        st.metric("🥑 脂質", f"{total_f:.1f} g")
        st.metric("🍚 炭水化物", f"{total_c:.1f} g")

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[total_p, total_f, total_c],
            theta=["たんぱく質", "脂質", "炭水化物"],
            fill="toself"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(total_p, total_f, total_c) + 10])),
            showlegend=False,
            title="🕸️ PFCバランス"
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    if store_input:
        st.warning("該当する店舗が見つかりません。")

st.caption("📁 CSVファイルは60秒ごとに自動更新されます。")
