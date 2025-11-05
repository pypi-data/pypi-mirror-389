# krx300_hj3415/adapters/services/excel.py
import asyncio
from pathlib import Path
import pandas as pd
from loguru import logger


async def read_excel_to_df(path: Path) -> pd.DataFrame:
    # pandas는 동기 → 스레드 오프로딩
    def _read():
        # xls의 경우 xlrd==1.2.0 필요
        return pd.read_excel(
            path,
            usecols="B:I",
            skiprows=2,
            dtype={"종목코드": "string", "종목명": "string"},
        )
    df = await asyncio.to_thread(_read)

    # 정제: 코드 6자리 보장, 원화예금 제거
    df["종목코드"] = df["종목코드"].astype("string").str.strip().str.zfill(6)
    before = len(df)
    df = df[df["종목명"].astype("string").str.strip() != "원화예금"].copy()
    logger.info(f"엑셀 로드/정제 완료: {len(df)} rows (removed {before-len(df)})")
    return df

