
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import difflib

def hira_to_kata(text):
    return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in text])

def get_candidates(user_input, store_names):
    katakana_input = hira_to_kata(user_input)
    candidates = []
    for s in store_names:
        scores = []
        if katakana_input in s:
            scores.append(s.index(katakana_input))
        if user_input in s:
            scores.append(s.index(user_input))
        sim = difflib.SequenceMatcher(None, s, katakana_input).ratio()
        if scores or sim > 0.5:
            candidates.append((s, min(scores) if scores else 99, -sim))
    return [x[0] for x in sorted(candidates, key=lambda x: (x[1], x[2]))]

df = pd.read_csv("menu_data_all_chains.csv")

st.set_page_config(page_title="PFCチェーンメニュー", layout="centered")
st.title("PFCチェーンメニュー検索")

store_input = st.text_input("店舗名を入力してください（ひらがなでも可）")
store = None
if store_input:
    candidates = get_candidates(store_input, df["店舗名"].unique())
    if candidates:
        store = st.selectbox("候補店舗を選んでください", candidates)

if store:
    filtered_df = df[df["店舗名"] == store]
    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
    cols = [col for col in filtered_df.columns if col != "店舗名"]
    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=400
    )
    selected_rows = grid_response["selected_rows"]
    if selected_rows:
        selected_df = pd.DataFrame(selected_rows)
        total = selected_df[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.markdown(
            f"### ✅ 選択メニューの合計\n"
            f"- カロリー: **{total['カロリー']:.0f}kcal**\n"
            f"- たんぱく質: **{total['たんぱく質 (g)']:.1f}g**\n"
            f"- 脂質: **{total['脂質 (g)']:.1f}g**\n"
            f"- 炭水化物: **{total['炭水化物 (g)']:.1f}g**"
        )
else:
    st.info("店舗名を入力してください（ひらがな可）。")
