import requests
CSV_URL = "https://github.com/oimoemu/pfc-mcdonalds-auto/raw/main/menu_data_all_chains.csv"
with open("menu_data_all_chains.csv", "wb") as f:
    f.write(requests.get(CSV_URL).content)
import requests
CSV_URL = "https://github.com/oimoemu/pfc-mcdonalds-auto/raw/main/menu_data_all_chains.csv"
with open("menu_data_all_chains.csv", "wb") as f:
    f.write(requests.get(CSV_URL).content)
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv
import unidecode
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm

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
    roma = unidecode.unidecode(text)  # ローマ字化
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

    # カテゴリ選択
    category_options = store_df["カテゴリ"].dropna().unique().tolist()
    category = st.selectbox("カテゴリを選択してください", ["（全て表示）"] + category_options)

    # カテゴリでフィルタ
    if category == "（全て表示）":
        filtered_df = store_df.copy()
    else:
        filtered_df = store_df[store_df["カテゴリ"] == category]

    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # インデックスをリセットし、row_id列を生成
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["row_id"] = filtered_df.index.astype(str)

    # 表示カラムリスト（カテゴリを除く）
    cols = [col for col in filtered_df.columns if col not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字", "row_id", "カテゴリ"]]

    # 選択状態をrow_idで管理
    selected_key = "selected_row_ids"
    if selected_key not in st.session_state:
        st.session_state[selected_key] = []

    prev_selected_ids = st.session_state[selected_key]

    # カスタムstyle
    menu_cell_style_jscode = JsCode("""
        function(params) {
            let text = params.value || '';
            let size = '0.95em';
            if (text.length > 16) {
                size = '0.8em';
            }
            if (text.length > 32) {
                size = '0.7em';
            }
            return {
                'font-size': size,
                'font-weight': 'bold',
                'white-space': 'pre-wrap',
                'line-height': '1.1'
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

    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols + ["row_id"]])
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("メニュー名", cellStyle=menu_cell_style_jscode, width=200, minWidth=200, maxWidth=260, pinned="left", resizable=False)
    for col in cols:
        if col != "メニュー名":
            gb.configure_column(col, width=36, minWidth=20, maxWidth=60, resizable=False, cellStyle=cell_style_jscode)
    gb.configure_column("row_id", hide=True)

    # 行IDをrow_idに（getRowNodeId）
    grid_options = gb.build()
    grid_options['getRowNodeId'] = JsCode("function(data){ return data['row_id']; }")
    grid_options['rowHeight'] = 40  # ← ここを追加！（好きな高さに調整OK）
    row_height = 40
    num_rows = len(filtered_df)
    table_height = max(min(num_rows, 12), 8) * row_height + 60  # 8行以上12行以下で自動

    grid_options['rowHeight'] = row_height

    grid_response = AgGrid(
        filtered_df[cols + ["row_id"]],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        height=table_height,  # ここも自動計算
        allow_unsafe_jscode=True,
        pre_selected_rows=prev_selected_ids
    )

    # 選択row_idをセッションに保存
    selected_rows = grid_response["selected_rows"]
    if selected_rows is not None:
        st.session_state[selected_key] = [row.get("row_id") for row in selected_rows if isinstance(row, dict) and row.get("row_id") is not None]

    # ...（チェック状態のrow_idリスト更新は今のまま）...

# AgGrid選択row_idからdf全体の選択済みメニューを抽出
selected_df = df[df["row_id"].isin(st.session_state[selected_key])]

if not selected_df.empty:
    selected_names = selected_df["メニュー名"].tolist()
    st.markdown("### ✅ 選択されているメニュー名")
    for name in selected_names:
        st.write("・" + str(name))
    
    # 数値列だけ抜き出し、安全に合計
    pfc_cols = ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]
    for c in pfc_cols:
        if c not in selected_df.columns:
            selected_df[c] = 0
    total = selected_df[pfc_cols].apply(pd.to_numeric, errors='coerce').sum().fillna(0)

    st.markdown(
        f"### ✅ 選択メニューの合計\n"
        f"- カロリー: **{total.get('カロリー',0):.0f}kcal**\n"
        f"- たんぱく質: **{total.get('たんぱく質 (g)',0):.1f}g**\n"
        f"- 脂質: **{total.get('脂質 (g)',0):.1f}g**\n"
        f"- 炭水化物: **{total.get('炭水化物 (g)',0):.1f}g**"
    )

    # PFC円グラフ
    pfc_vals = [
        total.get("たんぱく質 (g)", 0),
        total.get("脂質 (g)", 0),
        total.get("炭水化物 (g)", 0)
    ]
    if sum(pfc_vals) > 0:
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
            # textprops={'fontsize': 10, 'fontproperties': prop} # ← prop使うなら定義必須
        )
        ax.set_title("PFCバランス")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("PFC値が0のため円グラフを表示できません")
else:
    st.info("左端のチェックを選択してください")


else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")

