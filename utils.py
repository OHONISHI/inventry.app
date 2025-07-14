"""
画面表示以外の様々な機能の関数を定義するファイル
"""
import streamlit as st
import pandas as pd
import os

# 🔹 CSVファイルのパス
DATA_FILE = "inventory.csv"
COLUMNS   = ["品番", "品名", "数量"]   # 固定ヘッダー

def _ensure_data_file() -> None:
    """CSV が無い or 中身ゼロのとき、ヘッダー付きで作成する"""
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        pd.DataFrame(columns=COLUMNS).to_csv(
            DATA_FILE, index=False, encoding="utf-8-sig"
        )

# データ読み込み
def load_data() -> pd.DataFrame:
    """常に DataFrame を返す ― 空でもエラーにしない"""
    _ensure_data_file()
    try:
        return pd.read_csv(DATA_FILE, dtype=str)
    except pd.errors.EmptyDataError:
        # ヘッダーのみ存在していても例外が出ることがあるので保険
        return pd.DataFrame(columns=COLUMNS)
    
# データ保存
def save_data(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    
# 全在庫データを辞書リストで取得
def get_stocks():
    return load_data().to_dict(orient="records")


# 新しい物品を登録
def add_stock(stock_number, stock_name):
    stock_number = str(stock_number)
    df = load_data()
    if stock_number in df["品番"].values:
        existing_name = df.loc[df["品番"] == stock_number, "品名"].values[0]
        st.error(f"品番「{stock_number}」品名「{existing_name}」は既に存在します。")
        return
    df.loc[len(df)] = [stock_number, stock_name, 0]
    save_data(df)
    st.success(f"品番「{stock_number}」品名「{stock_name}」を登録しました。")


# 在庫一覧
def stock_list():
    df = load_data()
    if df.empty:
        st.write("現在、登録されている在庫はありません。")
    else:
        st.write("在庫一覧")
        st.dataframe(df)


# 出庫処理
def remove_stock(stock_number, quantity):
    stock_number = str(stock_number)
    df = load_data()
    for index, row in df.iterrows():
        if row["品番"] == stock_number:
            current_quantity = int(row["数量"])
            if current_quantity < quantity:
                st.warning(f"品番「{stock_number}」品名「{row['品名']}」は在庫不足です。")
                return
            df.at[index, "数量"] = str(current_quantity - quantity)
            save_data(df)
            st.success(f"品番「{stock_number}」品名「{row['品名']}」を{quantity}個出庫しました。")
            return
    st.error(f"品番「{stock_number}」は見つかりませんでした。")


# 入庫処理
def add_stock_quantity(stock_number, quantity):
    stock_number = str(stock_number)
    df = load_data()
    for index, row in df.iterrows():
        if row["品番"] == stock_number:
            new_quantity = int(row["数量"]) + int(quantity)
            df.at[index, "数量"] = str(new_quantity)
            save_data(df)
            st.success(f"品番「{stock_number}」品名「{row['品名']}」を{quantity}個入庫しました。")
            return
    st.error(f"品番「{stock_number}」は見つかりませんでした。")


# 削除処理
def delete_stock(stock_number):
    stock_number = str(stock_number)
    df = load_data()
    updated_df = df[df["品番"] != stock_number]
    if len(updated_df) == len(df):
        st.warning(f"品番「{stock_number}」は在庫に存在しません。")
        return
    save_data(updated_df)
    st.success(f"品番「{stock_number}」を削除しました。")
