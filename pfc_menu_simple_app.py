import streamlit as st
import pandas as pd
import jaconv
import unidecode
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ▼ フォント設定
fontpath = "fonts/NotoSansJP-Regular.ttf"
if not os.path.isfile(fontpath):
    st.error(f"指定フォントが見つかりません: {fontpath}")
prop = fm.FontProperties(fname=fontpath)

# ▼ データ読み込み
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

# ▼ グローバルCSS：追加欄50px・メニュー名10px＋折り返し
st.markdown("""
<style>
/* 追加欄 */
[data-testid="stDataFrame"] table td:nth-child(1),
[data-testid="stDataFrame"] table th:nth-child(1) {
    min-width: 50px !important;
    max-width: 50px !important;
    width: 50px !important;
    text-align: center !important;
}
/* メニュー名（2列目）*/
[data-testid="stDataFrame"] table td:nth-child(2),
[data-testid="stDataFrame"] table th:nth-child(2) {
    font-size: 10px !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    min-width: 120px !important;
    max-width: 220px !important;
}
/* PFC（3列目以降）*/
[data-testid="stDataFrame"] table td:nth-child(n+3),
[data-testid="stDataFrame"] table th:nth-child(n+3) {
    font-size: 10px !important;
    min-width: 60px !important;
    max-width: 80px !important;
}
</style>
""", unsafe_allow_html=True)

# ▼ （ここに店舗名入力～検索～絞り込みまで挿入OK）
# --- ここでは全データを例示 ---
pfc_cols = [col for col in ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"] if col in df.columns]
show_cols = ["メニュー名"] + pfc_cols
df_show = df[show_cols].copy()
df_show.insert(0, "追加", False)

# ▼ 列幅指定
col_cfg = {
    "追加": st.column_config.CheckboxColumn(label="追加", width="xxsmall"),
    "メニュー名": st.column_config.TextColumn(label="メニュー名", width="medium"),
}
for c in pfc_cols:
    col_cfg[c] = st.column_config.NumberColumn(label=c, width="small")

edited = st.data_editor(
    df_show,
    use_container_width=True,
    hide_index=True,
    column_config=col_cfg,
    height=540
)

added = edited[edited["追加"]]
st.write("✅ 追加済みメニュー", added)

if not added.empty:
    total = added[pfc_cols].sum()
    st.write("### 追加メニューの合計")
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
    st.info("「追加」列をチェックしてください")
