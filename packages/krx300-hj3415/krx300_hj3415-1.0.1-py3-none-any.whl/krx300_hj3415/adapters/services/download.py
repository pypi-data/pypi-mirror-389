# krx300_hj3415/adapters/services/download.py
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from random import uniform

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from krx300_hj3415.adapters.constants import URL_TPL, MAX_LOOKBACK_DAYS, MIN_BYTES, TEMP_DIR
from loguru import logger

def _looks_like_excel(resp: httpx.Response) -> bool:
    ctype = (resp.headers.get("Content-Type") or "").lower()
    cdisp = (resp.headers.get("Content-Disposition") or "").lower()
    size_ok = resp.num_bytes_downloaded is not None and resp.num_bytes_downloaded > MIN_BYTES
    excel_hint = any(x in ctype for x in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]) or re.search(r'\.(xlsx?|xlsb)\b', cdisp) is not None
    not_html = "text/html" not in ctype
    return bool(size_ok and not_html and excel_hint)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.6, min=0.6, max=3),
    retry=retry_if_exception_type(httpx.TransportError),
    reraise=True,
)
async def _get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    return await client.get(url)

async def find_valid_url(client: httpx.AsyncClient, max_days: int = MAX_LOOKBACK_DAYS) -> str:
    for d in range(1, max_days + 1):
        ymd = (datetime.now() - timedelta(days=d)).strftime("%Y%m%d")
        url = URL_TPL.format(ymd=ymd)
        try:
            resp = await _get(client, url)
            if resp.is_success and _looks_like_excel(resp):
                logger.info(f"[FOUND] {url} (len≈{resp.num_bytes_downloaded})")
                return url
            else:
                logger.warning(f"[SKIP] {url} CT={resp.headers.get('Content-Type')} len={resp.num_bytes_downloaded}")
        except Exception as e:
            logger.error(f"[ERROR] GET {url}: {e}")
        await asyncio.sleep(uniform(0.6, 1.6))  # 약한 지연
    raise RuntimeError("유효한 KRX300 엑셀 URL을 찾지 못했습니다.")

async def download_excel(client: httpx.AsyncClient) -> Path | None:
    # temp 초기화
    def _reset_temp():
        import shutil
        import os
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
    await asyncio.to_thread(_reset_temp)
    logger.info(f"임시폴더 초기화: {TEMP_DIR}")

    try:
        url = await find_valid_url(client)
        resp = await _get(client, url)
        if not (resp.is_success and _looks_like_excel(resp)):
            logger.error(f"다운로드 실패 또는 엑셀 아님: CT={resp.headers.get('Content-Type')} len={resp.num_bytes_downloaded}")
            return None

        ymd = url.split("gijunYMD=")[-1][:8]
        # 간단 확장자 추정
        ext = ".xlsx" if "openxmlformats" in (resp.headers.get("Content-Type") or "").lower() else ".xls"
        path = TEMP_DIR / f"{ymd}{ext}"
        # 파일 저장(동기→to_thread)
        await asyncio.to_thread(path.write_bytes, resp.content)
        logger.info(f"엑셀 저장: {path}")
        return path
    except Exception as e:
        logger.error(f"엑셀 다운로드 중 오류: {e}")
        return None