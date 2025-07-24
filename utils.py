"""
画面表示以外の様々な機能の関数を定義するファイル
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import csv
from logger import logger


# 🔹 CSVファイルのパス
DATA_FILE = "inventory.csv"
COLUMNS   = ["品番", "品名", "数量","単位"]   # 固定ヘッダー

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
def add_stock(stock_number, stock_name, unit):
    stock_number = str(stock_number)[:6]  # 品番は最大6文字
    df = load_data()
    if stock_number in df["品番"].values:
        existing_name = df.loc[df["品番"] == stock_number, "品名"].values[0]
        logger.warning(f"登録失敗: 品番「{stock_number}」品名「{existing_name}」は既に存在します。")
        st.error(f"品番「{stock_number}」品名「{existing_name}」は既に存在します。")
        return
    df.loc[len(df)] = [stock_number, stock_name, 0, unit]  # 数量は初期値0
    save_data(df)
    logger.info(f"新規登録: 品番「{stock_number}」品名「{stock_name}」（単位：{unit}）")
    st.success(f"品番「{stock_number}」品名「{stock_name}」（単位：{unit}）を登録しました。")


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
    stock_number = str(stock_number)[:6]  # 品番は最大6文字
    df = load_data()
    for index, row in df.iterrows():
        if row["品番"] == stock_number:
            current_quantity = int(row["数量"])
            if current_quantity < quantity:
                st.warning(f"品番「{stock_number}」品名「{row['品名']}」は在庫不足です。")
                return
            df.at[index, "数量"] = str(current_quantity - quantity)
            save_data(df)
            unit = row["単位"]
            save_history("出庫", stock_number, row["品名"], quantity, unit)
            # 🔽 order.csv に追記
            write_order_record(stock_number=stock_number, stock_name=row["品名"], quantity=quantity, unit=unit)
            logger.info(f"出庫完了: {stock_number} - {quantity}{unit}")
            st.success(f"品番「{stock_number}」品名「{row['品名']}」を{quantity}{unit}出庫しました。")
            return
    logger.warning(f"在庫不足または品番未登録: {stock_number}")
    st.error(f"品番「{stock_number}」は見つかりませんでした。")


ORDER_FILE = "order.csv"

# 🔹 order.csv が無ければヘッダー付きで作成
def _ensure_order_file():
    """order.csv が無ければヘッダー付きで作成"""
    if not os.path.exists(ORDER_FILE) or os.path.getsize(ORDER_FILE) == 0:
        header = ["日付", "品番", "品名", "数量", "単位"]
        pd.DataFrame(columns=header).to_csv(ORDER_FILE, index=False, encoding="utf-8-sig")


# 🔽 出庫内容を order.csv に記録する関数
def write_order_record(stock_number, stock_name, quantity, unit, file_path=ORDER_FILE):
    _ensure_order_file()
    header = ["日付", "品番", "品名", "数量", "単位"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [now, stock_number, stock_name, quantity, unit]
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(file_path) == 0:
            writer.writerow(header)  # ← ヘッダーを書き込む
        writer.writerow(row)


# 入庫処理
def add_stock_quantity(stock_number, quantity):
    stock_number = str(stock_number)[:6]  # 品番は最大6文字
    df = load_data()
    for index, row in df.iterrows():
        if row["品番"] == stock_number:
            new_quantity = int(row["数量"]) + int(quantity)
            df.at[index, "数量"] = str(new_quantity)
            save_data(df)
            unit = row["単位"]
            save_history("入庫", stock_number, row["品名"], quantity, unit)
            logger.info(f"入庫完了: {stock_number} - {quantity}{unit}")    
            st.success(f"品番「{stock_number}」品名「{row['品名']}」を{quantity}{unit}入庫しました。")
            # 🔽🔽🔽 ここから追加：order.csv から古い出庫記録を削除
            try:
                if os.path.exists(ORDER_FILE) and os.path.getsize(ORDER_FILE) > 0:
                    order_df = pd.read_csv(ORDER_FILE, encoding="utf-8-sig", dtype=str)
                    # 対象品番でフィルタして、古い順にソート
                    target_rows = order_df[order_df["品番"] == stock_number].sort_values("日付")
                    if not target_rows.empty:
                        delete_count = min(quantity, len(target_rows))  # 削除する最大行数
                        order_df = order_df.drop(target_rows.index[:delete_count])
                        order_df.to_csv(ORDER_FILE, index=False, encoding="utf-8-sig")
                        logger.info(f"order.csvから{delete_count}件の出庫記録を削除しました。")
            except Exception as e:
                logger.warning(f"order.csv の削除処理中にエラーが発生: {e}")
            # 🔼🔼🔼 ここまで追加
            return
    logger.warning(f"在庫不足または品番未登録: {stock_number}")    
    st.error(f"品番「{stock_number}」は見つかりませんでした。")
    return


# 削除処理
def delete_stock(stock_number):
    stock_number = str(stock_number)[:6]  # 品番は最大6文字
    df = load_data()
    updated_df = df[df["品番"] != stock_number]
    if len(updated_df) == len(df):
        logger.warning(f"削除失敗: 品番「{stock_number}」は在庫に存在しません。")
        st.warning(f"品番「{stock_number}」は在庫に存在しません。")
        return
    save_data(updated_df)
    logger.info(f"品番「{stock_number}」を削除しました。")
    st.success(f"品番「{stock_number}」を削除しました。")

# 履歴管理
HISTORY_FILE = "history.csv"
HISTORY_COLUMNS = ["日時", "操作", "品番", "品名", "数量", "単位"]

def _ensure_history_file():
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

def save_history(operation, stock_number, stock_name, quantity=None, unit=None):
    _ensure_history_file()
    #現在の日時
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    # 履歴読み込み
    df = pd.read_csv(HISTORY_FILE)
    # 2週間以上前の履歴を削除
    if not df.empty:
        try:
            df = df.copy()
            df["日時"] = pd.to_datetime(df["日時"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
            two_weeks_ago = now - timedelta(weeks=2)
            df = df[df["日時"] >= two_weeks_ago]  # 残すのは2週間以内の履歴のみ
        except Exception as e:
            logger.error("履歴の日付処理に失敗しました:", e)
    new_record = {
        "日時": now_str,
        "操作": operation,
        "品番": stock_number,
        "品名": stock_name,
        "数量": quantity if quantity is not None else "",
        "単位": unit if unit is not None else "",
    }
    df.loc[len(df)] = new_record
    # 保存
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")


