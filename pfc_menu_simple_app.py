import streamlit as st
import pandas as pd
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

# ...（省略：検索・店舗選択ロジックはそのまま）...
# filtered_df = ...（検索・絞り込み済みDataFrame）

# 必要な表示列
pfc_cols = [col for col in ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"] if col in df.columns]
show_cols = ["メニュー名"] + pfc_cols
df_show = filtered_df[show_cols].copy()
df_show.insert(0, "追加", False)  # ←「追加」列（Boolean）

# ▼ グローバルCSSで追加欄40px幅＆メニュー名10px小フォント強制
st.markdown("""
<style>
/* 追加欄（1列目） */
[data-testid="stDataFrame"] table td:nth-child(1),
[data-testid="stDataFrame"] table th:nth-child(1) {
    min-width: 40px !important;
    max-width: 40px !important;
    width: 40px !important;
    text-align: center !important;
}
/* メニュー名（2列目）は10pxで折り返し */
[data-testid="stDataFrame"] table td:nth-child(2),
[data-testid="stDataFrame"] table th:nth-child(2) {
    font-size: 10px !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    min-width: 100px !important;
    max-width: 220px !important;
}
</style>
""", unsafe_allow_html=True)

# 列幅指定
col_cfg = {
    "追加": st.column_config.CheckboxColumn(label="追加", width="xxsmall"),  # チェックボックスは大きさそのまま
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
