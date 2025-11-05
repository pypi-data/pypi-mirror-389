# krx300_hj3415/constants.py

from pathlib import Path

TABLE_NAME = "krx300"
BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "krx.db"
TEMP_DIR = BASE_DIR / "temp"

URL_TPL = "https://www.samsungfund.com/excel_pdf.do?fId=2ETFA4&gijunYMD={ymd}"
MAX_LOOKBACK_DAYS = 15

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
MIN_BYTES = 4096  # 이보다 작으면 에러 페이지/빈 파일일 확률↑