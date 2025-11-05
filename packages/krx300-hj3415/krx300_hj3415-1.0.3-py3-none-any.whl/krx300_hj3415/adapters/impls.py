# krx300_hj3415/adapters/impls.py
from pathlib import Path
import pandas as pd
import httpx
from typing import Sequence, Optional, Any

from krx300_hj3415.adapters.clients.http import new_client
from krx300_hj3415.adapters.services.download import download_excel
from krx300_hj3415.adapters.services.excel import read_excel_to_df
from krx300_hj3415.adapters.repos.sqlite_repo import replace_table, get_codes
from krx300_hj3415.adapters.repos.hashutil import file_sha256
from krx300_hj3415.adapters.repos.state_store import CodesStore

from krx300_hj3415.core.ports import (
    HttpClient, ExcelDownloader, ExcelReader, CodesRepo, Hasher, CodesStorePort
)

class DefaultHttpClient:
    def __init__(self):
        self._client = new_client()
    @property
    def raw(self) -> httpx.AsyncClient:
        return self._client
    async def aclose(self) -> None:
        await self._client.aclose()

class Downloader(ExcelDownloader):
    async def download(self, client: HttpClient) -> Path:
        return await download_excel(client.raw)

class Reader(ExcelReader):
    async def to_dataframe(self, xls_path: Path) -> pd.DataFrame:
        return await read_excel_to_df(xls_path)

class Repo(CodesRepo):
    async def replace_table(self, df: pd.DataFrame) -> None:
        await replace_table(df)
    async def get_codes(self) -> Sequence[str]:
        return await get_codes()

class HasherImpl(Hasher):
    def file_sha256(self, path: Path) -> Optional[str]:
        try:
            return file_sha256(path)
        except Exception:
            return None

class CodesStoreAdapter(CodesStorePort):
    def __init__(self, state_path: Path):
        self._store = CodesStore(state_path)
    async def load_snapshot(self) -> dict[str, Any]:
        return await self._store.load_snapshot()
    async def save(self, codes: Sequence[str], *, source_ymd: str, etag: Optional[str]) -> Path:
        await self._store.save(codes, source_ymd=source_ymd, etag=etag)
        return self._store.path