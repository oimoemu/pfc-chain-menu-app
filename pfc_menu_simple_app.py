
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv
import unidecode

df = pd.read_csv("menu_data_all_chains.csv")
if "カロリー" not in df.columns:
    df["カロリー"] = 0

def get_yomi(text):
    hira = jaconv.kata2hira(jaconv.z2h(str(text), kana=True, digit=False, ascii=False))
    kata = jaconv.hira2kata(hira)
    roma = unidecode.unidecode(text)  # ローマ字化
    return hira, kata, roma.lower()

if not all(col in df.columns for col in ["店舗よみ", "店舗カナ", "店舗ローマ字"]):
    df["店舗よみ"], df["店舗カナ"], df["店舗ローマ字"] = zip(*df["店舗名"].map(get_yomi))

st.set_page_config(page_title="PFCチェーンメニュー", layout="centered")
st.title("PFCチェーンメニュー検索")

st.markdown("""
    <style>
    .ag-header-cell-label {
        font-size: 0.8em !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

store_input = st.text_input("店舗名を入力（ひらがな・カタカナ・英語・一部でも可）", value="", key="store_search")
candidates = []
if len(store_input) > 0:
    hira = jaconv.kata2hira(jaconv.z2h(store_input, kana=True, digit=False, ascii=False))
    kata = jaconv.hira2kata(hira)
    roma = unidecode.unidecode(store_input).lower()
    match = df[
        df["店舗よみ"].str.contains(hira)
        | df["店舗カナ"].str.contains(kata)
        | df["店舗名"].str.contains(store_input)
        | df["店舗ローマ字"].str.contains(roma)
    ].店舗名.unique().tolist()
    candidates = match[:10]
if len(candidates) == 0 and store_input:
    st.warning("該当する店舗がありません")
if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None
if len(candidates) > 0:
    st.markdown("#### 候補店舗（クリックで選択）")
    for c in candidates:
        if st.button(c, key=f"select_{c}"):
            st.session_state["selected_store"] = c
store = st.session_state.get("selected_store", None)

if store:
    st.success(f"選択店舗：{store}")
    filtered_df = df[df["店舗名"] == store]
    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
    cols = [col for col in filtered_df.columns if col not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字"]]
    cell_style_jscode = JsCode("""
    function(params) {
        if (params.colDef.field === 'メニュー名') {
            return {
                'font-size': '1.1em',
                'font-weight': 'bold',
                'white-space': 'pre-wrap'
            }
        }
        return {'font-size': '0.8em', 'max-width': '36px', 'white-space': 'pre-wrap', 'padding': '1px'};
    }
    """)
    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("メニュー名", cellStyle=cell_style_jscode, width=500, pinned="left", resizable=False)
    for col in cols:
        if col != "メニュー名":
            gb.configure_column(col, width=36, resizable=False, cellStyle=cell_style_jscode)
    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        height=430,
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
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
        