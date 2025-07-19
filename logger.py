# logger.py
import logging

LOG_FILE = "app.log"

# ロガーを作成
logger = logging.getLogger("stock_app")
logger.setLevel(logging.INFO)

# 出力形式を設定
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ファイル出力ハンドラー
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# コンソール出力（必要なら）
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)

# 重複追加防止
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)
