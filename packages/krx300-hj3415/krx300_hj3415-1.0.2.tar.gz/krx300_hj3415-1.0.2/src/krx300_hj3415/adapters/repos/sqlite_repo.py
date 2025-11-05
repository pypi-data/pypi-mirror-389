# krx300_hj3415/adapters/repos/sqlite_repo.py

import asyncio
import sqlite3
from typing import List, Tuple
import pandas as pd
from krx300_hj3415.adapters.constants import SQLITE_PATH, TABLE_NAME
from loguru import logger

async def replace_table(df: pd.DataFrame) -> None:
    def _write():
        conn = sqlite3.connect(SQLITE_PATH)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_code ON "{TABLE_NAME}"("종목코드");')
            conn.commit()
        finally:
            conn.close()
    await asyncio.to_thread(_write)
    logger.info(f"SQLite 테이블 교체 완료: {SQLITE_PATH.name}:{TABLE_NAME}")

async def get_codes() -> List[str]:
    def _read() -> List[str]:
        with sqlite3.connect(SQLITE_PATH) as conn:
            q = f'SELECT 종목코드 FROM "{TABLE_NAME}" WHERE 종목코드 LIKE "______"'
            df = pd.read_sql(q, conn, dtype={"종목코드": "string"})
            return df["종목코드"].astype("string").str.strip().str.zfill(6).dropna().tolist()
    return await asyncio.to_thread(_read)

async def get_code_names() -> List[Tuple[str, str]]:
    def _read() -> List[Tuple[str, str]]:
        with sqlite3.connect(SQLITE_PATH) as conn:
            q = f'SELECT 종목코드, 종목명 FROM "{TABLE_NAME}" WHERE 종목코드 LIKE "______"'
            df = pd.read_sql(q, conn, dtype={"종목코드": "string", "종목명": "string"})
            df["종목코드"] = df["종목코드"].astype("string").str.strip().str.zfill(6)
            df["종목명"] = df["종목명"].astype("string").fillna("")
            return list(df.itertuples(index=False, name=None))
    return await asyncio.to_thread(_read)

async def get_name(code: str) -> str | None:
    code = (code or "").strip().zfill(6)
    def _read_one() -> str | None:
        with sqlite3.connect(SQLITE_PATH) as conn:
            row = conn.execute(f'SELECT 종목명 FROM "{TABLE_NAME}" WHERE 종목코드 = ?', (code,)).fetchone()
            return row[0] if row and row[0] else None
    return await asyncio.to_thread(_read_one)