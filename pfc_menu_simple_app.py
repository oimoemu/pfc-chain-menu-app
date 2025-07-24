
import streamlit as st
import pandas as pd

# グローバルに検索語入力欄を一度だけ定義
検索語 = st.text_input("店舗名を入力", key="店舗検索欄").strip().lower()
st.session_state["検索語"] = 検索語
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import jaconv
import unidecode
import matplotlib.pyplot as plt

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

import jaconv
from unidecode import unidecode

# 初期状態
if "ページ" not in st.session_state:
    st.session_state["ページ"] = "店舗検索"
if "検索語" not in st.session_state:
    st.session_state["検索語"] = ""
if "選択店舗" not in st.session_state:
    st.session_state["選択店舗"] = ""

def get_yomi(text):
    hira = jaconv.kata2hira(jaconv.z2h(str(text), kana=True, digit=False, ascii=False))
    roma = unidecode(text)
    return hira.lower(), roma.lower()

def 店舗検索ページ():
    店舗一覧 = sorted(df["店舗名"].dropna().unique())

    候補店舗 = []
    for 店舗 in 店舗一覧:
        よみ, ローマ = get_yomi(店舗)
        if (検索語 in 店舗.lower()) or (検索語 in よみ) or (検索語 in ローマ):
            候補店舗.append(店舗)

    if not 候補店舗:
        st.info("該当する店舗が見つかりません")
    else:
        選択店舗 = st.selectbox("該当する店舗を選んでください", 候補店舗, key="店舗候補選択")
        if st.button("✅ この店舗を選ぶ", key=f"btn_{選択店舗}"):
            st.session_state["選択店舗"] = 選択店舗
            st.session_state["ページ"] = "メニュー表示"
            st.experimental_rerun()

def メニュー表示ページ():
    選択店舗 = st.session_state["選択店舗"]
    st.header(f"🍽 {選択店舗} のメニュー")
    filtered_df = df[df["店舗名"] == 選択店舗]

    if st.button("🔙 店舗を再選択", key="btn_back"):
        st.session_state["ページ"] = "店舗検索"
        st.experimental_rerun()

    カテゴリ一覧 = sorted(filtered_df["カテゴリ"].dropna().unique())
    選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)
    if 選択カテゴリ != "すべて":
        filtered_df = filtered_df[filtered_df["カテゴリ"] == 選択カテゴリ]

    sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
    sort_order = st.radio("並び替え順", ["高い順", "低い順"])
    ascending = sort_order == "低い順"
    filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)

    選択メニュー = st.multiselect("PFCを集計するメニューを選択", filtered_df["メニュー名"].tolist())
    選択df = filtered_df[filtered_df["メニュー名"].isin(選択メニュー)]

    st.dataframe(filtered_df)

    if not 選択df.empty:
        total_p = 選択df["たんぱく質"].sum()
        total_f = 選択df["脂質"].sum()
        total_c = 選択df["炭水化物"].sum()

        st.markdown("### ✅ 選択メニューのPFC合計")
        st.markdown(f"- たんぱく質：{total_p:.1f} g")
        st.markdown(f"- 脂質：{total_f:.1f} g")
        st.markdown(f"- 炭水化物：{total_c:.1f} g")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        labels = ["たんぱく質", "脂質", "炭水化物"]
        values = [total_p, total_f, total_c]
        colors = ["#66b3ff", "#ff9999", "#99ff99"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("メニューを選択するとPFC合計と円グラフが表示されます。")

# ページ分岐実行
if st.session_state["ページ"] == "店舗検索":
    店舗検索ページ()
elif st.session_state["ページ"] == "メニュー表示":
    メニュー表示ページ()



import jaconv
from unidecode import unidecode

# 初期状態の管理
if "ページ" not in st.session_state:
    st.session_state["ページ"] = "店舗検索"
if "検索語" not in st.session_state:
    st.session_state["検索語"] = ""
if "選択店舗" not in st.session_state:
    st.session_state["選択店舗"] = ""

# 店舗名を曖昧検索する補助関数
def get_yomi(text):
    hira = jaconv.kata2hira(jaconv.z2h(str(text), kana=True, digit=False, ascii=False))
    roma = unidecode(text)
    return hira.lower(), roma.lower()

# ページ1：店舗検索
if st.session_state["ページ"] == "店舗検索":
    店舗一覧 = sorted(df["店舗名"].dropna().unique())

    候補店舗 = []
    for 店舗 in 店舗一覧:
        よみ, ローマ = get_yomi(店舗)
        if (検索語 in 店舗.lower()) or (検索語 in よみ) or (検索語 in ローマ):
            候補店舗.append(店舗)

    if not 候補店舗:
        st.info("該当する店舗が見つかりません")
    else:
        選択店舗 = st.selectbox("該当する店舗を選んでください", 候補店舗, key="店舗候補選択")
        if st.button("この店舗を選ぶ"):
            st.session_state["選択店舗"] = 選択店舗
            st.session_state["ページ"] = "メニュー表示"
            st.experimental_rerun()

# ページ2：メニュー表示
elif st.session_state["ページ"] == "メニュー表示":
    選択店舗 = st.session_state["選択店舗"]
    st.header(f"🍽 {選択店舗} のメニュー")
    df = df[df["店舗名"] == 選択店舗]

    if st.button("🔙 店舗を再選択"):
        st.session_state["ページ"] = "店舗検索"
        st.experimental_rerun()

    カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
    選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)
    if 選択カテゴリ != "すべて":
        df = df[df["カテゴリ"] == 選択カテゴリ]

    sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
    sort_order = st.radio("並び替え順", ["高い順", "低い順"])
    ascending = sort_order == "低い順"
    df = df.sort_values(by=sort_column, ascending=ascending)

    選択メニュー = st.multiselect("PFCを集計するメニューを選択", df["メニュー名"].tolist())
    選択df = df[df["メニュー名"].isin(選択メニュー)]

    st.dataframe(df)

    if not 選択df.empty:
        total_p = 選択df["たんぱく質"].sum()
        total_f = 選択df["脂質"].sum()
        total_c = 選択df["炭水化物"].sum()

        st.markdown("### ✅ 選択メニューのPFC合計")
        st.markdown(f"- たんぱく質：{total_p:.1f} g")
        st.markdown(f"- 脂質：{total_f:.1f} g")
        st.markdown(f"- 炭水化物：{total_c:.1f} g")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        labels = ["たんぱく質", "脂質", "炭水化物"]
        values = [total_p, total_f, total_c]
        colors = ["#66b3ff", "#ff9999", "#99ff99"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("メニューを選択するとPFC合計と円グラフが表示されます。")



import jaconv
from unidecode import unidecode

# ページ状態を管理（最初は店舗選択ページ）
if "店舗選択済み" not in st.session_state:
    st.session_state["店舗選択済み"] = False
    st.session_state["選択店舗"] = ""

def get_yomi(text):
    hira = jaconv.kata2hira(jaconv.z2h(str(text), kana=True, digit=False, ascii=False))
    roma = unidecode(text)
    return hira.lower(), roma.lower()

if not st.session_state["店舗選択済み"]:
    st.header("🔍 店舗名検索（曖昧対応）")

    # 店舗一覧とよみ・ローマ字辞書を作成
    店舗一覧 = sorted(df["店舗名"].dropna().unique())
    検索語 = st.text_input("店舗名を入力（ひらがな・カタカナ・漢字・英語対応）", key="店舗検索_入力欄").strip().lower()

    候補店舗 = []
    for 店舗 in 店舗一覧:
        よみ, ローマ = get_yomi(店舗)
        if (検索語 in 店舗.lower()) or (検索語 in よみ) or (検索語 in ローマ):
            候補店舗.append(店舗)
    if not 候補店舗:
        st.warning("該当する店舗が見つかりませんでした。")
        st.stop()

    選択店舗 = st.selectbox("該当する店舗を選んでください", 候補店舗)

    if st.button("この店舗を選ぶ"):
        st.session_state["店舗選択済み"] = True
        st.session_state["選択店舗"] = 選択店舗
        st.experimental_rerun()
else:
    # メニュー画面（店舗選択済み）
    選択店舗 = st.session_state["選択店舗"]
    st.header(f"🍽 {選択店舗} のメニュー")

    df = df[df["店舗名"] == 選択店舗]

    # カテゴリ選択
    カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
    選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)
    if 選択カテゴリ != "すべて":
        df = df[df["カテゴリ"] == 選択カテゴリ]

    # 並び替え
    sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
    sort_order = st.radio("並び替え順", ["高い順", "低い順"])
    ascending = sort_order == "低い順"
    df = df.sort_values(by=sort_column, ascending=ascending)

    # メニュー選択
    選択メニュー = st.multiselect("PFCを集計するメニューを選択", df["メニュー名"].tolist())
    選択df = df[df["メニュー名"].isin(選択メニュー)]

    st.dataframe(df)

    if not 選択df.empty:
        total_p = 選択df["たんぱく質"].sum()
        total_f = 選択df["脂質"].sum()
        total_c = 選択df["炭水化物"].sum()

        st.markdown(f"### ✅ 選択メニューのPFC合計")
        st.markdown(f"- たんぱく質：{total_p:.1f} g")
        st.markdown(f"- 脂質：{total_f:.1f} g")
        st.markdown(f"- 炭水化物：{total_c:.1f} g")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        labels = ["たんぱく質", "脂質", "炭水化物"]
        values = [total_p, total_f, total_c]
        colors = ["#66b3ff", "#ff9999", "#99ff99"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("メニューを選択するとPFC合計と円グラフが表示されます。")



# ページ状態を管理（最初は店舗選択ページ）
if "店舗選択済み" not in st.session_state:
    st.session_state["店舗選択済み"] = False
    st.session_state["選択店舗"] = ""

if not st.session_state["店舗選択済み"]:
    st.header("🔍 店舗名検索")

    店舗一覧 = sorted(df["店舗名"].dropna().unique())
    検索語 = st.text_input("店舗名を入力（ひらがな・カタカナ・漢字・英語対応）", key="店舗検索_入力欄").strip().lower()

    if 検索語:
        候補店舗 = [s for s in 店舗一覧 if 検索語 in s.lower()]
    else:
        候補店舗 = 店舗一覧

    選択店舗 = st.selectbox("該当する店舗を選んでください", 候補店舗)

    if st.button("この店舗を選ぶ"):
        st.session_state["店舗選択済み"] = True
        st.session_state["選択店舗"] = 選択店舗
        st.experimental_rerun()
else:
    # メニュー画面（店舗選択済み）
    選択店舗 = st.session_state["選択店舗"]
    st.header(f"🍽 {選択店舗} のメニュー")

    df = df[df["店舗名"] == 選択店舗]

    # カテゴリ選択
    カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
    選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)
    if 選択カテゴリ != "すべて":
        df = df[df["カテゴリ"] == 選択カテゴリ]

    # 並び替え
    sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
    sort_order = st.radio("並び替え順", ["高い順", "低い順"])
    ascending = sort_order == "低い順"
    df = df.sort_values(by=sort_column, ascending=ascending)

    # メニュー選択
    選択メニュー = st.multiselect("PFCを集計するメニューを選択", df["メニュー名"].tolist())
    選択df = df[df["メニュー名"].isin(選択メニュー)]

    st.dataframe(df)

    if not 選択df.empty:
        total_p = 選択df["たんぱく質"].sum()
        total_f = 選択df["脂質"].sum()
        total_c = 選択df["炭水化物"].sum()

        st.markdown(f"### ✅ 選択メニューのPFC合計")
        st.markdown(f"- たんぱく質：{total_p:.1f} g")
        st.markdown(f"- 脂質：{total_f:.1f} g")
        st.markdown(f"- 炭水化物：{total_c:.1f} g")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        labels = ["たんぱく質", "脂質", "炭水化物"]
        values = [total_p, total_f, total_c]
        colors = ["#66b3ff", "#ff9999", "#99ff99"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("メニューを選択するとPFC合計と円グラフが表示されます。")



if 選択店舗 != "すべて":
    df = df[df["店舗名"] == 選択店舗]




if 選択店舗 != "すべて":
    df = df[df["店舗名"] == 選択店舗]


# カテゴリ選択（店舗＋検索で絞った後のカテゴリ）
カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)

if 選択カテゴリ != "すべて":
    df = df[df["カテゴリ"] == 選択カテゴリ]

# 並び替え
sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
sort_order = st.radio("並び替え順", ["高い順", "低い順"])
ascending = sort_order == "低い順"
df = df.sort_values(by=sort_column, ascending=ascending)

# メニュー選択
選択メニュー = st.multiselect("PFCを集計するメニューを選択", df["メニュー名"].tolist())
選択df = df[df["メニュー名"].isin(選択メニュー)]

# メニュー表示
st.dataframe(df)

# 選択メニューのPFC合計と円グラフ
if not 選択df.empty:
    total_p = 選択df["たんぱく質"].sum()
    total_f = 選択df["脂質"].sum()
    total_c = 選択df["炭水化物"].sum()

    st.markdown(f"### ✅ 選択メニューのPFC合計")
    st.markdown(f"- たんぱく質：{total_p:.1f} g")
    st.markdown(f"- 脂質：{total_f:.1f} g")
    st.markdown(f"- 炭水化物：{total_c:.1f} g")

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    labels = ["たんぱく質", "脂質", "炭水化物"]
    values = [total_p, total_f, total_c]
    colors = ["#66b3ff", "#ff9999", "#99ff99"]
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("メニューを選択するとPFC合計と円グラフが表示されます。")



# 店舗名で検索入力
店舗検索 = st.text_input("店舗名で検索（ひらがな・カタカナ・漢字など）").strip()
if 店舗検索:
    df = df[df["店舗名"].str.contains(店舗検索, case=False, na=False)]

# カテゴリ選択（検索後のカテゴリ一覧）
カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)
if 選択カテゴリ != "すべて":
    df = df[df["カテゴリ"] == 選択カテゴリ]

# 並び替え
sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
sort_order = st.radio("並び替え順", ["高い順", "低い順"])
ascending = sort_order == "低い順"
df = df.sort_values(by=sort_column, ascending=ascending)

# メニュー選択
選択メニュー = st.multiselect("PFCを集計するメニューを選択", df["メニュー名"].tolist())
選択df = df[df["メニュー名"].isin(選択メニュー)]

# メニュー表示
st.dataframe(df)

# 選択メニューのPFC合計
if not 選択df.empty:
    total_p = 選択df["たんぱく質"].sum()
    total_f = 選択df["脂質"].sum()
    total_c = 選択df["炭水化物"].sum()

    st.markdown(f"### ✅ 選択メニューのPFC合計")
    st.markdown(f"- たんぱく質：{total_p:.1f} g")
    st.markdown(f"- 脂質：{total_f:.1f} g")
    st.markdown(f"- 炭水化物：{total_c:.1f} g")

    # 円グラフ
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    labels = ["たんぱく質", "脂質", "炭水化物"]
    values = [total_p, total_f, total_c]
    colors = ["#66b3ff", "#ff9999", "#99ff99"]
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("メニューを選択するとPFC合計と円グラフが表示されます。")



# 店舗名を選択
店舗一覧 = sorted(df["店舗名"].dropna().unique())
選択店舗 = st.selectbox("店舗名を選んでください", ["すべて"] + 店舗一覧)

if 選択店舗 != "すべて":
    df = df[df["店舗名"] == 選択店舗]

# カテゴリ選択（店舗フィルター後のカテゴリを抽出）
カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)

if 選択カテゴリ != "すべて":
    df = df[df["カテゴリ"] == 選択カテゴリ]

# 並び替え
sort_column = st.selectbox("並び替え項目", ["たんぱく質", "脂質", "炭水化物", "カロリー"])
sort_order = st.radio("並び替え順", ["高い順", "低い順"])
ascending = sort_order == "低い順"
df = df.sort_values(by=sort_column, ascending=ascending)

# メニュー表示
st.dataframe(df)

# 合計表示
total_p = df["たんぱく質"].sum()
total_f = df["脂質"].sum()
total_c = df["炭水化物"].sum()

st.markdown(f"### PFC合計")
st.markdown(f"- たんぱく質：{total_p:.1f} g")
st.markdown(f"- 脂質：{total_f:.1f} g")
st.markdown(f"- 炭水化物：{total_c:.1f} g")

# 円グラフで表示
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
labels = ["たんぱく質", "脂質", "炭水化物"]
values = [total_p, total_f, total_c]
colors = ["#66b3ff", "#ff9999", "#99ff99"]
ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
ax.axis("equal")
st.pyplot(fig)


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


# カテゴリフィルター追加
カテゴリ一覧 = sorted(df["カテゴリ"].dropna().unique())
選択カテゴリ = st.selectbox("カテゴリを選んでください", ["すべて"] + カテゴリ一覧)

# カテゴリに応じてフィルター処理
if 選択カテゴリ != "すべて":
    df = df[df["カテゴリ"] == 選択カテゴリ]


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
    filtered_df = df[df["店舗名"] == store]
    keyword = st.text_input("メニュー名で絞り込み（例：チーズ/カレーなど）")
    if keyword:
        filtered_df = filtered_df[filtered_df["メニュー名"].str.contains(keyword, case=False)]
    sort_by = st.radio("並び替え基準", ["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"], horizontal=True)
    ascending = st.radio("並び順", ["昇順", "降順"], horizontal=True) == "昇順"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
    
    # row_id列追加（indexでOK）
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["row_id"] = filtered_df.index.astype(str)

    cols = [col for col in filtered_df.columns if col not in ["店舗名", "店舗よみ", "店舗カナ", "店舗ローマ字", "row_id"]]
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
    
    # --- 選択状態をrow_idで管理 ---
    selected_key = "selected_row_ids"
    if selected_key not in st.session_state:
        st.session_state[selected_key] = []

    prev_selected_ids = st.session_state[selected_key]

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

    grid_response = AgGrid(
        filtered_df[cols + ["row_id"]],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        height=430,
        allow_unsafe_jscode=True,
        pre_selected_rows=prev_selected_ids
    )
    selected_rows = grid_response["selected_rows"]
    # 選択row_idをセッションに保存
    if selected_rows is not None:
        st.session_state[selected_key] = [row.get("row_id") for row in selected_rows if isinstance(row, dict) and row.get("row_id") is not None]
    if selected_rows is not None and len(selected_rows) > 0:
        selected_df = pd.DataFrame(selected_rows)
        total = selected_df[["カロリー", "たんぱく質 (g)", "脂質 (g)", "炭水化物 (g)"]].sum()
        st.markdown(
            f"### ✅ 選択メニューの合計\n"
            f"- カロリー: **{total['カロリー']:.0f}kcal**\n"
            f"- たんぱく質: **{total['たんぱく質 (g)']:.1f}g**\n"
            f"- 脂質: **{total['脂質 (g)']:.1f}g**\n"
            f"- 炭水化物: **{total['炭水化物 (g)']:.1f}g**"
        )

        # ★ここからPFCバランス円グラフ
        pfc_vals = [total["たんぱく質 (g)"], total["脂質 (g)"], total["炭水化物 (g)"]]
        pfc_labels = ["たんぱく質", "脂質", "炭水化物"]
        fig, ax = plt.subplots()
        ax.pie(pfc_vals, labels=pfc_labels, autopct="%.1f%%", startangle=90, counterclock=False)
        ax.set_title("PFCバランス")
        st.pyplot(fig)
else:
    st.info("店舗名を入力してください（ひらがな・カタカナ・英語もOK）")
        