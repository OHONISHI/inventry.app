import streamlit as st
import pandas as pd
import utils as utils
from logger import logger

st.title("在庫管理システム")

st.sidebar.title("メニュー")
selected_item = st.sidebar.radio("モードを選択してください", ("物品在庫一覧","入庫","出庫","物品登録","物品削除","履歴"))

if selected_item == "物品在庫一覧":
    st.subheader("物品在庫一覧")
    if st.button("在庫一覧を表示"):
        utils.stock_list()

elif selected_item == "入庫":
    st.subheader("入庫")
    # セッション変数初期化
    if "found_stock_name_in" not in st.session_state:
        st.session_state.found_stock_name_in = None
    if "last_stock_number_in" not in st.session_state:
        st.session_state.last_stock_number_in = ""
    stock_number = st.text_input("品番を入力してください: ").strip()
    # 入力変更時のみ再チェック
    if stock_number != st.session_state.last_stock_number_in:
        st.session_state.found_stock_name_in = None
        st.session_state.last_stock_number_in = stock_number
        for stock in utils.get_stocks():  # 毎回最新を取得
            if stock["品番"] == stock_number:
                st.session_state.found_stock_name_in = stock["品名"]
                break
        else:
            st.warning(f"品番「{stock_number}」は登録されていません。")
    # 商品名表示（あれば）
    if st.session_state.found_stock_name_in:
        st.write(f"「{st.session_state.found_stock_name_in}」")
    # 数量入力＋ボタン
    quantity = st.number_input("追加する数量を入力してください: ", min_value=1)
    if st.button("入庫"):
        if st.session_state.found_stock_name_in:
            utils.add_stock_quantity(stock_number, quantity)
        else:
            st.error("登録されていない品番には入庫できません。")


elif selected_item == "出庫":
    st.subheader("出庫")
    if "found_stock_name_out" not in st.session_state:
        st.session_state.found_stock_name_out = None
    if "last_stock_number_out" not in st.session_state:
        st.session_state.last_stock_number_out = ""
    stock_number = st.text_input("品番を入力してください: ").strip()
    if stock_number and stock_number != st.session_state.last_stock_number_out:
        st.session_state.found_stock_name_out = None
        st.session_state.last_stock_number_out = stock_number
        for stock in utils.get_stocks():  # 毎回最新を取得
            if stock["品番"] == stock_number:
                st.session_state.found_stock_name_out = stock["品名"]
                break
        else:
            st.warning(f"品番「{stock_number}」は登録されていません。")
    if st.session_state.found_stock_name_out:
        st.write(f"「{st.session_state.found_stock_name_out}」")
    quantity = st.number_input("出庫する数量を入力してください: ", min_value=1)
    if st.button("出庫"):
        if st.session_state.found_stock_name_out:
            utils.remove_stock(stock_number, quantity)
        else:
            st.error("登録されていない品番には出庫できません。")


elif selected_item == "物品登録":
    st.subheader("物品登録")
    stock_number = st.text_input("品番（例: A001）")
    stock_name = st.text_input("品名（例: ボールペン）")
    unit = st.text_input("単位（例: 箱、個）")
    if st.button("登録"):
        utils.add_stock(stock_number, stock_name, unit)

elif selected_item == "物品削除":
    st.subheader("物品削除")
    # 初期化（ページ切り替え時のみ）
    if "found_stock_name" not in st.session_state:
        st.session_state.found_stock_name = None
    if "delete_done" not in st.session_state:
        st.session_state.delete_done = False
    # 入力
    stock_number = st.text_input("削除する品番を入力してください（例: A001）").strip()
    # 入力変更時に状態をリセット
    if stock_number != st.session_state.get("last_input_stock_number", ""):
        st.session_state.found_stock_name = None
        st.session_state.delete_done = False
        st.session_state.last_input_stock_number = stock_number
        # 該当品番の確認
        if stock_number:
            for stock in utils.get_stocks():  # 毎回最新を取得
                if stock["品番"] == stock_number:
                    st.session_state.found_stock_name = stock["品名"]
                    break
            else:
                st.warning(f"品番「{stock_number}」は登録されていません。")
    # 対象が見つかっていれば表示
    if st.session_state.found_stock_name:
        st.write(f"「{st.session_state.found_stock_name}」")
    # 確認チェックボックス
    confirm = st.checkbox("本当に削除しますか？")
    # 削除ボタン
    if st.button("削除"):
        if st.session_state.found_stock_name and confirm:
            utils.delete_stock(stock_number)
            st.session_state.delete_done = True
            st.session_state.found_stock_name = None
        else:
            st.error("登録されていない品番、または確認チェックが必要です。")

elif selected_item == "履歴":
    st.subheader("操作履歴")
    try:
        history_df = pd.read_csv("history.csv")
        if history_df.empty:
            st.info("履歴がまだ記録されていません。")
        else:
            st.dataframe(history_df)
    except FileNotFoundError:
        st.info("履歴ファイルがまだ存在していません。")

