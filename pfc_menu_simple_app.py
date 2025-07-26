import streamlit as st
import pandas as pd
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

# カスタムCSS
st.markdown("""
<style>
.menu-cell {
    max-width: 180px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 1em;
    line-height: 1.2em;
    min-height: 32px;
    max-height: 48px;
    overflow: hidden;
    display: flex;
    align-items: center;
}
.menu-cell.small {
    font-size: 0.8em !important;
}
.menu-cell.xsmall {
    font-size: 0.65em !important;
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

    # メニュー名列を長さに応じて自動フォントサイズ縮小・折り返し
    def render_menu_name(name):
        if len(str(name)) > 25:
            return f'<div class="menu-cell xsmall">{str(name)}</div>'
        elif len(str(name)) > 14:
            return f'<div class="menu-cell small">{str(name)}</div>'
        else:
            return f'<div class="menu-cell">{str(name)}</div>'

    df_show["メニュー名"] = df_show["メニュー名"].apply(render_menu_name)

    # 列幅指定
    col_cfg = {
        "選択": st.column_config.CheckboxColumn(label="選択", width="small"),
        "メニュー名": st.column_config.MarkdownColumn(label="メニュー名", width="medium"),
    }
    for pfc in pfc_cols:
        col_cfg[pfc] = st.column_config.NumberColumn(label=pfc, width="small")

    # データエディタで表示
    edited = st.data_editor(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_config=col_cfg,
        height=540
    )

    # 選択された行のみ抽出
    selected = edited[edited["選択"]]
    st.write("✅ 選択中のメニュー", selected)

    # 合計と円グラフ
    if not selected.empty:
        total = selected[pfc_cols].sum()
        st.write("### 選択メニューの合計")
        if "カロリー" in total: st.write(f"カロリー: {total['カロリー']:.0f}kcal")
        if "たんぱく質 (g)" in total: st.write(f"たんぱく質: {total['たんぱく質 (g)']:.1f}g")
        if "脂質 (g)" in total: st.write(f"脂質: {total['脂質 (g)']:.1f}g")
        if "炭水化物 (g)" in total: st.write(f"炭水化物: {total['炭水化物 (g)']:.1f}g")

        # PFCバランス円グラフ
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
