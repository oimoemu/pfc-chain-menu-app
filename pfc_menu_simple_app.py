
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


def hira_to_kata(text):
    return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in text])


def hira_to_kata(text):
    return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in text])


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


store_input = st.text_input("店舗名を入力してください（ひらがなでも可）")
store = None
if store_input:
    katakana_input = hira_to_kata(store_input)
    candidates = [s for s in df["店舗名"].unique() if katakana_input in s or store_input in s]
    sorted_candidates = sorted(candidates, key=lambda x: min(x.find(katakana_input), x.find(store_input)))
    if sorted_candidates:
        store = st.selectbox("候補店舗を選んでください", sorted_candidates)



if store is not None:
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

    
    # 表表示（AgGridで選択可能に）
    cols = [col for col in filtered_df.columns if col != "店舗名"]
    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=400,
        enable_enterprise_modules=False
    )

    selected_rows = grid_response["selected_rows"]
    if selected_rows:
        selected_df = pd.DataFrame(selected_rows)
        total = selected_df[["たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.markdown(
            "### ✅ 選択メニューの合計PFC\n- たんぱく質: **{:.1f}g**\n- 脂質: **{:.1f}g**\n- 炭水化物: **{:.1f}g**".format(
                total[0], total[1], total[2]
            )
        )
