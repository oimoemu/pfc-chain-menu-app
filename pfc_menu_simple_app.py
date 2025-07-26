import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import jaconv
import unidecode
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

fontpath = "fonts/NotoSansJP-Regular.ttf"
if not os.path.isfile(fontpath):
    st.error(f"指定フォントが見つかりません: {fontpath}")
prop = fm.FontProperties(fname=fontpath)

df = pd.read_csv("menu_data_all_chains.csv")
if "カロリー" not in df.columns:
    df["カロリー"] = 0

def get_yomi(text):
    hira = jaconv.kata2hira(jaconv.z2h(str(text), kana=True, digit=False, ascii=False))
    kata = jaconv.hira2kata(hira)
    roma = unidecode.unidecode(text)
    return hira, kata, roma.lower()

if not all(col in df.columns for col in ["店舗よみ", "店舗カナ", "店舗ローマ字"]):
    df["店舗よみ"], df["店舗カナ"], df["店舗ローマ字"] = zip(*df["店舗名"].map(get_yomi))

st.set_page_config(page_title="PFCチェーンメニュー", layout="wide")
st.title("PFCチェーンメニュー検索")

st.markdown("""
    <style>
    .ag-header-cell-label {
        font-size: 0.8em !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    .ag-row {
        height: 48px !important;
        min-height: 48px !important;
        max-height: 48px !important;
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
    store_df = df[df["店舗名"] == store]

    category_options = store_df["カテゴリ"].dropna().unique().tolist()
    category = st.selectbox("カテゴリを選択してください", ["（全て表示）"] + category_options)

    if category == "（全て表示）":
        filtered_df = store_df.copy()
    else:
        filtered_df = store_df[store_df["カテゴリ"] == category]

    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    if sort_by in filtered_df.columns and not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    if filtered_df.empty:
        st.info("選択された条件ではメニューが見つかりません。")
        st.stop()
    
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["row_id"] = filtered_df.index.astype(str)

    # --------- チェックボックス列を追加 ----------
    if "選択" not in filtered_df.columns:
        filtered_df.insert(0, "選択", False)

    # 表示列
    cols = [col for col in filtered_df.columns if col not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字", "row_id", "カテゴリ"]]
    display_cols = ["選択", "メニュー名"] + [col for col in cols if col not in ["選択", "メニュー名"]]

    menu_cell_style_jscode = JsCode("""
        function(params) {
            let text = params.value || '';
            let size = '0.95em';
            if (text.length > 14) { size = '0.85em'; }
            if (text.length > 22) { size = '0.75em'; }
            return {
                'font-size': size,
                'font-weight': 'bold',
                'white-space': 'pre-wrap',
                'line-height': '22px',
                'minHeight': '48px',
                'maxHeight': '48px',
                'display': 'flex',
                'align-items': 'center'
            }
        }
    """)
    cell_style_jscode = JsCode("""
        function(params) {
            return {
                'font-size': '0.8em',
                'max-width': '36px',
                'white-space': 'pre-wrap',
                'padding': '1px'
            }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(filtered_df[display_cols + ["row_id"]])
    # 「選択」列はeditableでチェックボックスになる
    gb.configure_column("選択", editable=True, type=["boolean"], width=48)
    gb.configure_column("row_id", hide=True)
    gb.configure_column("メニュー名", cellStyle=menu_cell_style_jscode, width=200, minWidth=180, maxWidth=280, resizable=False)
    for col in display_cols:
        if col not in ["選択", "メニュー名"]:
            gb.configure_column(col, width=36, minWidth=20, maxWidth=60, resizable=False, cellStyle=cell_style_jscode)

    grid_options = gb.build()
    grid_options['rowHeight'] = 48
    grid_options['getRowNodeId'] = JsCode("function(data){ return data['row_id']; }")

    grid_response = AgGrid(
        filtered_df[display_cols + ["row_id"]],
        gridOptions=grid_options,
        update_mode="MODEL_CHANGED",
        fit_columns_on_grid_load=False,
        height=440,
        allow_unsafe_jscode=True
    )

    # 選択行の取得
    df_checked = pd.DataFrame(grid_response["data"])
    checked = df_checked[df_checked["選択"] == True]
    if not checked.empty:
        total = checked[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.markdown(
            f"### ✅ 選択メニューの合計\n"
            f"- カロリー: **{total['カロリー']:.0f}kcal**\n"
            f"- たんぱく質: **{total['たんぱく質 (g)']:.1f}g**\n"
            f"- 脂質: **{total['脂質 (g)']:.1f}g**\n"
            f"- 炭水化物: **{total['炭水化物 (g)']:.1f}g**"
        )

        # PFC円グラフ
        pfc_vals = [total["たんぱく質 (g)"], total["脂質 (g)"], total["炭水化物 (g)"]]
        pfc_labels = ["たんぱく質", "脂質", "炭水化物"]
        colors = ["#4e79a7", "#f28e2b", "#e15759"]
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            pfc_vals,
            labels=pfc_labels,
            autopct="%.1f%%",
            startangle=90,
            counterclock=False,
            colors=colors,
            textprops={'fontsize': 10, 'fontproperties': prop}
        )
        ax.set_title("PFCバランス", fontproperties=prop)
        for text, color in zip(texts, colors):
            text.set_color(color)
            text.set_fontproperties(prop)
        plt.tight_layout()
        st.pyplot(fig)
else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
