
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import difflib
import jaconv

def hira_to_kata(text):
    return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in text])

def get_yomi(text):
    try:
        return jaconv.hira2kata(jaconv.kata2hira(jaconv.z2h(text, kana=True, digit=False, ascii=False)))
    except:
        return text

def get_candidates(user_input, store_names):
    katakana_input = hira_to_kata(user_input)
    user_input_kana = get_yomi(user_input)
    candidates = []
    for s in store_names:
        s_kana = get_yomi(s)
        hit_score = 999
        for pat in [user_input, katakana_input, user_input_kana]:
            if pat and pat in s:
                hit_score = min(hit_score, s.index(pat))
            if pat and pat in s_kana:
                hit_score = min(hit_score, s_kana.index(pat))
        sim = max(
            difflib.SequenceMatcher(None, s, user_input).ratio(),
            difflib.SequenceMatcher(None, s_kana, user_input_kana).ratio()
        )
        if hit_score < 999 or sim > 0.6:
            candidates.append((s, hit_score, -sim))
    return [x[0] for x in sorted(candidates, key=lambda x: (x[1], x[2]))]

df = pd.read_csv("menu_data_all_chains.csv")
if "カロリー" not in df.columns:
    df["カロリー"] = 0

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

    cell_style_jscode = JsCode("""
    function(params) {
        if (params.colDef.field === 'メニュー名') {
            return {
                'font-size': '1.4em',
                'font-weight': 'bold',
                'white-space': 'pre-wrap'
            }
        }
        return {};
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("メニュー名", cellStyle=cell_style_jscode, width=260)
    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=420,
        allow_unsafe_jscode=True
    )
    selected_rows = grid_response["selected_rows"]
    if selected_rows is not None and len(selected_rows) > 0:
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
        