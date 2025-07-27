
import streamlit as st
import pandas as pd
import jaconv
import unidecode
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
st.markdown("""
<style>
/* まず全体を小フォント化（10px） */
[data-testid="stDataFrame"] table, 
[data-testid="stDataFrame"] table td, 
[data-testid="stDataFrame"] table th {
    font-size: 10px !important;
    line-height: 1.1 !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    vertical-align: top !important;
}
/* メニュー名列（2列目）だけさらに小さく（8.5px）・幅狭・詰める */
[data-testid="stDataFrame"] table td:nth-child(2),
[data-testid="stDataFrame"] table th:nth-child(2) {
    font-size: 8.5px !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    min-width: 70px !important;
    max-width: 140px !important;
    line-height: 1.05 !important;
    padding-top: 1px !important;
    padding-bottom: 1px !important;
    vertical-align: top !important;
}
</style>
""", unsafe_allow_html=True)
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

# グローバルCSS：列幅を固定・折り返し・フォント縮小
st.markdown("""
<style>
th, td {
    max-width: 100px !important;  /* カロリー/PFCは狭く */
    min-width: 50px !important;
    white-space: pre-wrap !important;
    word-break: break-all !important;
    font-size: 12px !important;
}
td:nth-child(2), th:nth-child(2) {
    max-width: 210px !important;  /* メニュー名だけ幅広く固定 */
    min-width: 150px !important;
    font-size: 11px !important;
}
td, th {
    line-height: 1.15 !important;
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

    # 列順・サイズ指定
    pfc_cols = [col for col in ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"] if col in filtered_df.columns]
    df_show = filtered_df[["メニュー名"] + pfc_cols].copy()
    df_show.insert(0, "選択", False)

    # 列幅と型のカスタム
    col_cfg = {
        "選択": st.column_config.CheckboxColumn(label="選択", width="small"),
        "メニュー名": st.column_config.TextColumn(label="メニュー名", width="medium"),
    }
    for pfc in pfc_cols:
        col_cfg[pfc] = st.column_config.NumberColumn(label=pfc, width="small")

    edited = st.data_editor(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_config=col_cfg,
        height=540
    )

    selected = edited[edited["選択"]]
    st.write("✅ 選択中のメニュー", selected)

    if not selected.empty:
        total = selected[pfc_cols].sum()
        st.write("### 選択メニューの合計")
        if "カロリー" in total: st.write(f"カロリー: {total['カロリー']:.0f}kcal")
        if "たんぱく質 (g)" in total: st.write(f"たんぱく質: {total['たんぱく質 (g)']:.1f}g")
        if "脂質 (g)" in total: st.write(f"脂質: {total['脂質 (g)']:.1f}g")
        if "炭水化物 (g)" in total: st.write(f"炭水化物: {total['炭水化物 (g)']:.1f}g")

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
        st.info("左端のチェックを選択してください")

else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
