import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv, unidecode
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

# CSSで見た目もできるだけ小さく・多く見せる
st.markdown("""
<style>
.ag-row, .ag-cell, .ag-header-cell {
    font-size: 10px !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    line-height: 1.08 !important;
    padding-top: 1px !important;
    padding-bottom: 1px !important;
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

    # ここでBoolean「選択」列を用意
    if "選択" not in filtered_df.columns:
        filtered_df.insert(0, "選択", False)
    else:
        filtered_df["選択"] = filtered_df["選択"].astype(bool)

    # カラム定義
    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_column("選択", editable=True, type=["boolean"], cellEditor="agCheckboxCellEditor", width=50, pinned="left")
    gb.configure_column("メニュー名", width=180, minWidth=90, maxWidth=200)
    for col in ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]:
        if col in filtered_df.columns:
            gb.configure_column(col, width=70, minWidth=50, maxWidth=90)
    grid_options = gb.build()

    grid_response = AgGrid(
        filtered_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=False,
        height=540,
        allow_unsafe_jscode=True
    )

    # 選択済み行の取得
    checked_df = pd.DataFrame(grid_response["data"])
    selected_rows = checked_df[checked_df["選択"]]

    st.write("✅ 選択中のメニュー", selected_rows)

    if not selected_rows.empty:
        total = selected_rows[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.write("### 選択メニューの合計")
        st.write(f"カロリー: {total['カロリー']:.0f}kcal")
        st.write(f"たんぱく質: {total['たんぱく質 (g)']:.1f}g")
        st.write(f"脂質: {total['脂質 (g)']:.1f}g")
        st.write(f"炭水化物: {total['炭水化物 (g)']:.1f}g")
        # PFC円グラフ
        pfc_vals = [
            total.get("たんぱく質 (g)", 0),
            total.get("脂質 (g)", 0),
            total.get("炭水化物 (g)", 0)
        ]
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
        st.info("左端の「選択」をONにしてください")

else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
