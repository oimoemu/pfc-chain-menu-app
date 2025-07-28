import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv
import unidecode
import matplotlib.pyplot as plt

df = pd.read_csv("menu_data_all_chains.csv")
df = df.reset_index(drop=True)
df["row_id"] = df.index.astype(str)

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

selected_key = "selected_row_ids"
if selected_key not in st.session_state:
    st.session_state[selected_key] = []

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
        filtered_df = store_df[store_df["カテゴリ"] == category].copy()

    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]

    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    cols = [col for col in filtered_df.columns if col not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字", "カテゴリ"]]

    # 1. グローバルな「選択row_id」リスト（カテゴリ・ソートに関係なく保持）
    # 2. 今表示しているrow_idだけ抽出
    visible_row_ids = filtered_df["row_id"].tolist()
    pre_selected = [rid for rid in st.session_state[selected_key] if rid in visible_row_ids]

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

    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("メニュー名", cellStyle=menu_cell_style_jscode, width=200, minWidth=200, maxWidth=260, pinned="left", resizable=False)
    for col in cols:
        if col != "メニュー名" and col != "row_id":
            gb.configure_column(col, width=36, minWidth=20, maxWidth=60, resizable=False, cellStyle=cell_style_jscode)
    gb.configure_column("row_id", hide=True)

    grid_options = gb.build()
    grid_options['getRowNodeId'] = JsCode("function(data){ return data['row_id']; }")
    row_height = 40
    num_rows = len(filtered_df)
    table_height = max(min(num_rows, 12), 8) * row_height + 60
    grid_options['rowHeight'] = row_height

    # 3. AgGridには「pre_selected」に表示中の選択row_idだけ渡す
    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        height=table_height,
        allow_unsafe_jscode=True,
        pre_selected_rows=pre_selected
    )

    # 4. チェックボックスの追加/削除をグローバルリストに反映（非表示行はそのまま維持）
    selected_rows = grid_response["selected_rows"]
    if selected_rows is not None:
        now_selected_ids = set(row.get("row_id") for row in selected_rows if isinstance(row, dict) and row.get("row_id") is not None)
        before_selected_ids = set(st.session_state[selected_key])
        # 表示中でチェック外されたrow_idは除去、チェックされたrow_idは追加
        to_keep = (before_selected_ids - set(visible_row_ids)) | now_selected_ids
        st.session_state[selected_key] = list(to_keep)

    # 5. グローバルrow_idリストでdfから選択メニューを抽出
    selected_df = df[df["row_id"].isin(st.session_state[selected_key])]
    if not selected_df.empty:
        st.markdown("### ✅ 選択されているメニュー名")
        for name in selected_df["メニュー名"].tolist():
            st.write("・" + str(name))
        total = selected_df[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.markdown(
            f"### ✅ 選択メニューの合計\n"
            f"- カロリー: **{total['カロリー']:.0f}kcal**\n"
            f"- たんぱく質: **{total['たんぱく質 (g)']:.1f}g**\n"
            f"- 脂質: **{total['脂質 (g)']:.1f}g**\n"
            f"- 炭水化物: **{total['炭水化物 (g)']:.1f}g**"
        )
        pfc_vals = [total["たんぱく質 (g)"], total["脂質 (g)"], total["炭水化物 (g)"]]
        pfc_labels = ["たんぱく質", "脂質", "炭水化物"]
        fig, ax = plt.subplots()
        ax.pie(pfc_vals, labels=pfc_labels, autopct="%.1f%%", startangle=90, counterclock=False)
        ax.set_title("PFCバランス")
        st.pyplot(fig)
else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
