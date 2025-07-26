import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
import jaconv, unidecode
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# --- フォント指定 ---
fontpath = "fonts/NotoSansJP-Regular.ttf"
if not os.path.isfile(fontpath):
    st.error(f"指定フォントが見つかりません: {fontpath}")
prop = fm.FontProperties(fname=fontpath)

# --- データ読み込み ---
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

# --- 店舗選択などは省略（上のサンプル参照） ---
# ここでは「filtered_df」を作ったあとの部分から

# 例: 検索結果DataFrame
filtered_df = df.head(20).copy()  # デモ用。実装時は検索ロジックを使って！

# --- 各行に「追加」ボタン列を作る ---
filtered_df = filtered_df.reset_index(drop=True)
filtered_df["row_id"] = filtered_df.index.astype(str)
if "追加" not in filtered_df.columns:
    filtered_df["追加"] = ""

# --- 追加ボタン用のJSコード（AgGrid公式サンプルから）---
add_button_js = JsCode("""
    class BtnCellRenderer {
      init(params) {
        this.params = params;
        this.eGui = document.createElement('button');
        this.eGui.innerHTML = '追加';
        this.eGui.className = 'st-aggrid-btn';
        this.eGui.onclick = () => {
            window.dispatchEvent(
                new CustomEvent('streamlit:aggrid_add_row', {detail: {rowId: params.data.row_id}})
            );
        };
      }
      getGui() { return this.eGui; }
    }
""")

gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_column("追加", header_name="", cellRenderer=add_button_js, width=70, pinned="left")
for col in ["メニュー名", "カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]:
    if col in filtered_df.columns:
        gb.configure_column(col, width=120 if col == "メニュー名" else 60, resizable=True)

gb.configure_column("row_id", hide=True)
grid_options = gb.build()
grid_options['getRowNodeId'] = JsCode("function(data){ return data['row_id']; }")

# --- AgGrid表示 ---
grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    fit_columns_on_grid_load=False,
    update_mode=GridUpdateMode.NO_UPDATE,
    allow_unsafe_jscode=True,
    height=460,
    custom_js_events=["streamlit:aggrid_add_row"]
)

# --- セッションで「選択中リスト」を管理 ---
if "selected_row_ids" not in st.session_state:
    st.session_state["selected_row_ids"] = []

# --- JSイベント受信で「追加」 ---
if grid_response["custom_js_events"]:
    for event in grid_response["custom_js_events"]:
        if event["name"] == "streamlit:aggrid_add_row":
            row_id = event["detail"]["rowId"]
            if row_id not in st.session_state["selected_row_ids"]:
                st.session_state["selected_row_ids"].append(row_id)

# --- 「選択中リスト」の表示 ---
selected_rows = filtered_df[filtered_df["row_id"].isin(st.session_state["selected_row_ids"])]
st.write("### ✅ 選択中のメニュー", selected_rows)

# --- 合計とPFC円グラフ
if not selected_rows.empty:
    total = selected_rows[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
    st.write("### 選択メニューの合計")
    st.write(f"カロリー: {total['カロリー']:.0f}kcal")
    st.write(f"たんぱく質: {total['たんぱく質 (g)']:.1f}g")
    st.write(f"脂質: {total['脂質 (g)']:.1f}g")
    st.write(f"炭水化物: {total['炭水化物 (g)']:.1f}g")
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

# --- 選択済みリストから削除もやりたい場合は「削除」ボタンもリスト側で追加可 ---
