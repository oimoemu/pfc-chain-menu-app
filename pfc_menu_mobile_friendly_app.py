import streamlit as st
import pandas as pd

# ページ設定（サイドバーを折りたたみ）
st.set_page_config(
    page_title="PFCチェッカー",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="auto"
)

# カスタムCSS（スマホ対応含む）
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3 {
            color: #ff6600;
            font-weight: 700;
            font-size: 1.5rem;
        }
        .stDataFrame {
            font-size: 15px;
        }
        /* 表スクロール対応 */
        .stDataFrame > div {
            overflow-x: auto;
        }
        /* 表のヘッダー背景 */
        thead tr th {
            background-color: #f0f2f6;
            color: #333;
            font-weight: bold;
        }
        tbody tr:hover {
            background-color: #fcebd6;
        }
        /* セクション間スペース調整 */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# データ読み込み
@st.cache_data
def load_data():
    return pd.read_csv("menu_data_all.csv")  # ファイル名は実際のものに合わせて

df = load_data()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    selected_store = st.selectbox("店舗を選択", ["すべて"] + sorted(df["store"].unique()))
    sort_option = st.selectbox("並び替え基準", ["たんぱく質", "脂質", "炭水化物"])
    sort_order = st.radio("並び順", ["降順", "昇順"])

# フィルター処理
filtered_df = df.copy()
if selected_store != "すべて":
    filtered_df = filtered_df[filtered_df["store"] == selected_store]

ascending = sort_order == "昇順"
filtered_df = filtered_df.sort_values(by=sort_option, ascending=ascending)

# タイトル・説明
st.title("🍽️ 外食チェーンPFCチェッカー")
st.markdown("**外食メニューのPFC（たんぱく質・脂質・炭水化物）を一覧で表示・比較できます。スマホでも見やすく表示されます。**")

# 表の表示
st.subheader(f"📋 メニュー一覧（{selected_store if selected_store != 'すべて' else '全店舗'}）")
st.dataframe(
    filtered_df[["store", "menu", "たんぱく質", "脂質", "炭水化物"]].reset_index(drop=True),
    use_container_width=True
)

# フッター
st.markdown("---")
st.caption("© 2025 PFCチェッカー - モバイル対応済")


