# ── 最新CSVをGitHubから毎回取得（自動化） ─────────────────────────────
import requests
CSV_URL = "https://github.com/oimoemu/pfc-mcdonalds-auto/raw/main/menu_data_all_chains.csv"
with open("menu_data_all_chains.csv", "wb") as f:
    f.write(requests.get(CSV_URL).content)

# ── 通常インポート ─────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv
import unidecode
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm

# ── フォント（あれば使う／なければデフォルト） ──────────────────────
fontpath = "fonts/NotoSansJP-Regular.ttf"
prop = None
if os.path.isfile(fontpath):
    try:
        prop = fm.FontProperties(fname=fontpath)
    except Exception:
        prop = None

# ── データ読み込み（dfはここで一度だけ読む＆row_id付与） ─────────────
df = pd.read_csv("menu_data_all_chains.csv")
df = df.reset_index(drop=True)
df["row_id"] = df.index.astype(str)  # ← 全体で一意に固定（以後、再生成しない）
if "カロリー" not in df.columns:
    df["カロリー"] = 0

# かな・カナ・ローマ字検索用よみ列（無ければ生成）
def get_yomi(text):
    s = str(text)
    hira = jaconv.kata2hira(jaconv.z2h(s, kana=True, digit=False, ascii=False))
    kata = jaconv.hira2kata(hira)
    roma = unidecode.unidecode(s).lower()
    return hira, kata, roma

if not all(col in df.columns for col in ["店舗よみ", "店舗カナ", "店舗ローマ字"]):
    df["店舗よみ"], df["店舗カナ"], df["店舗ローマ字"] = zip(*df["店舗名"].map(get_yomi))

# ── Streamlit UI ───────────────────────────────────────────────────
st.set_page_config(page_title="PFCチェーンメニュー", layout="wide")
st.title("PFCチェーンメニュー検索")

# ヘッダ文字サイズ少し小さく
st.markdown("""
    <style>
    .ag-header-cell-label {
        font-size: 0.8em !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 店舗あいまい検索（ひらがな・カタカナ・英字・部分一致）
store_input = st.text_input("店舗名を入力（ひらがな・カタカナ・英語・一部でも可）", value="", key="store_search")
candidates = []
if store_input:
    hira = jaconv.kata2hira(jaconv.z2h(store_input, kana=True, digit=False, ascii=False))
    kata = jaconv.hira2kata(hira)
    roma = unidecode.unidecode(store_input).lower()
    match = df[
        df["店舗よみ"].str.contains(hira, na=False)
        | df["店舗カナ"].str.contains(kata, na=False)
        | df["店舗名"].str.contains(store_input, na=False)
        | df["店舗ローマ字"].str.contains(roma, na=False)
    ]["店舗名"].dropna().unique().tolist()
    candidates = match[:10]

if len(candidates) == 0 and store_input:
    st.warning("該当する店舗がありません")

if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None

if candidates:
    st.markdown("#### 候補店舗（クリックで選択）")
    cols_btn = st.columns(min(len(candidates), 2))
    for i, c in enumerate(candidates):
        if cols_btn[i % 2].button(c, key=f"select_{c}"):
            st.session_state["selected_store"] = c

store = st.session_state.get("selected_store")

# 全カテゴリ横断の選択row_idを保持
selected_key = "selected_row_ids"
if selected_key not in st.session_state:
    st.session_state[selected_key] = []

if store:
    st.success(f"選択店舗：{store}")
    store_df = df[df["店舗名"] == store].copy()

    # カテゴリ選択
    category_options = store_df["カテゴリ"].dropna().unique().tolist()
    category = st.selectbox("カテゴリを選択してください", ["（全て表示）"] + category_options)

    # カテゴリフィルタ（reset_indexしない！row_id再生成しない！）
    filtered_df = store_df if category == "（全て表示）" else store_df[store_df["カテゴリ"] == category]

    # メニュー名キーワード
    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False, na=False)]

    # 並び替え
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # 表示カラム（row_idは隠す／カテゴリ列は表示しない）
    cols = [c for c in filtered_df.columns if c not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字", "カテゴリ"]]

    # 可視行のrow_id と 事前選択
    visible_row_ids = filtered_df["row_id"].tolist()
    pre_selected = [rid for rid in st.session_state[selected_key] if rid in visible_row_ids]

    # セルスタイル
    menu_cell_style_jscode = JsCode("""
        function(params) {
            let text = params.value || '';
            let size = '0.95em';
            if (text.length > 16) size = '0.8em';
            if (text.length > 32) size = '0.7em';
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

    # AgGrid 構成
    gb = GridOptionsBuilder.from_dataframe(filtered_df[cols])
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_column("メニュー名", cellStyle=menu_cell_style_jscode,
                        width=200, minWidth=200, maxWidth=260, pinned="left", resizable=False)
    for c in cols:
        if c not in ["メニュー名", "row_id"]:
            gb.configure_column(c, width=36, minWidth=20, maxWidth=60, resizable=False, cellStyle=cell_style_jscode)
    gb.configure_column("row_id", hide=True)

    grid_options = gb.build()
    grid_options['getRowNodeId'] = JsCode("function(data){ return data['row_id']; }")
    row_height = 40
    num_rows = len(filtered_df)
    table_height = max(min(num_rows, 12), 8) * row_height + 60
    grid_options['rowHeight'] = row_height

    grid_response = AgGrid(
        filtered_df[cols],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        height=table_height,
        allow_unsafe_jscode=True,
        pre_selected_rows=pre_selected
    )

    # 選択のマージ保存（非表示は保持／可視の解除は反映）
    selected_rows = grid_response["selected_rows"]
    if selected_rows is not None:
        now_selected_ids = set(r.get("row_id") for r in selected_rows if isinstance(r, dict) and r.get("row_id"))
        before = set(st.session_state[selected_key])
        st.session_state[selected_key] = list((before - set(visible_row_ids)) | now_selected_ids)

    # df全体からrow_idで抽出して集計・可視化（カテゴリをまたいでも保持）
    selected_df = df[df["row_id"].isin(st.session_state[selected_key])]
    if not selected_df.empty:
        st.markdown("### ✅ 選択されているメニュー名")
        for name in selected_df["メニュー名"].tolist():
            st.write("・" + str(name))

        # 数値安全化して合計
        pfc_cols = ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]
        for c in pfc_cols:
            if c not in selected_df.columns:
                selected_df[c] = 0
        total = selected_df[pfc_cols].apply(pd.to_numeric, errors='coerce').sum().fillna(0)

        kcal = float(total.get("カロリー", 0) or 0)
        protein = float(total.get("たんぱく質 (g)", 0) or 0)
        fat = float(total.get("脂質 (g)", 0) or 0)
        carb = float(total.get("炭水化物 (g)", 0) or 0)

        st.markdown(
            f"### ✅ 選択メニューの合計\n"
            f"- カロリー: **{kcal:.0f}kcal**\n"
            f"- たんぱく質: **{protein:.1f}g**\n"
            f"- 脂質: **{fat:.1f}g**\n"
            f"- 炭水化物: **{carb:.1f}g**"
        )

        # 円グラフ（合計0なら表示しない）
        pfc_vals = [protein, fat, carb]
        if sum(pfc_vals) > 0:
            pfc_labels = ["たんぱく質", "脂質", "炭水化物"]
            colors = ["#4e79a7", "#f28e2b", "#e15759"]
            fig, ax = plt.subplots()
            if prop is not None:
                wedges, texts, autotexts = ax.pie(
                    pfc_vals, labels=pfc_labels, autopct="%.1f%%",
                    startangle=90, counterclock=False, colors=colors,
                    textprops={'fontsize': 10, 'fontproperties': prop}
                )
                ax.set_title("PFCバランス", fontproperties=prop)
                for text, color in zip(texts, colors):
                    text.set_color(color)
                    text.set_fontproperties(prop)
            else:
                ax.pie(pfc_vals, labels=pfc_labels, autopct="%.1f%%",
                       startangle=90, counterclock=False, colors=colors)
                ax.set_title("PFCバランス")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("PFC値が0のため円グラフを表示できません")
    else:
        st.info("左端のチェックを選択してください")
else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
