# krx300_hj3415/core/usecases/sync_snapshot.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from krx300_hj3415.adapters.clients.http import new_client
from krx300_hj3415.adapters.services.download import download_excel
from krx300_hj3415.adapters.services.excel import read_excel_to_df
from krx300_hj3415.adapters.repos.sqlite_repo import replace_table, get_codes
from krx300_hj3415.adapters.repos.hashutil import file_sha256
from krx300_hj3415.adapters.repos.state_store import CodesStore


@dataclass(frozen=True)
class SyncResult:
    ok: bool
    source_ymd: Optional[str]
    etag: Optional[str]
    saved_json: Optional[Path]
    rows: int
    added_codes: list[str]
    removed_codes: list[str]
    error: Optional[str] = None


class SyncSnapshotUseCase:
    """
    KRX300 스냅샷 동기화 유스케이스:
      1) 직전 스냅샷 로드
      2) 엑셀 URL 탐색/다운로드
      3) 엑셀 → DataFrame 정제
      4) SQLite 테이블 교체(인덱스 포함)
      5) SQLite에서 6자리 코드 재조회
      6) (이전 ↔ 현재) 코드 Diff 계산
      7) 상태 스냅샷(JSON) 저장
    """

    def __init__(
        self,
        *,
        state_path: Path,
        client: Optional[httpx.AsyncClient] = None,
        owns_client: bool = False,
    ) -> None:
        self.state_path = state_path
        self.client = client
        self.owns_client = owns_client

    @classmethod
    async def create(cls, *, state_path: Path) -> "SyncSnapshotUseCase":
        client = new_client()
        return cls(state_path=state_path, client=client, owns_client=True)

    async def run(self) -> SyncResult:
        if self.client is None:
            self.client = new_client()
            self.owns_client = True

        store = CodesStore(self.state_path)

        try:
            # 1) 직전 스냅샷 로드
            prev_snapshot = await store.load_snapshot()
            prev_codes = _normalize_code_list(prev_snapshot.get("codes", []))

            # 2) 다운로드
            xls_path = await download_excel(self.client)
            if not xls_path or not xls_path.exists():
                msg = "엑셀 파일 다운로드 실패"
                logger.error(msg)
                return SyncResult(False, None, None, None, 0, [], [], error=msg)

            source_ymd = _guess_ymd_from_filename(xls_path)
            logger.info(f"다운로드 완료: {xls_path} (source_ymd={source_ymd})")

            # 3) 해시(ETag 유사)
            try:
                etag = file_sha256(xls_path)
            except Exception as e:
                logger.warning(f"해시 계산 실패(계속 진행): {e}")
                etag = None

            # 4) 엑셀 → DF
            df = await read_excel_to_df(xls_path)
            rows = len(df)
            if rows == 0:
                msg = "엑셀 변환 결과가 비어 있습니다"
                logger.error(msg)
                return SyncResult(False, source_ymd, etag, None, 0, [], [], error=msg)

            # 5) SQLite 교체
            await replace_table(df)

            # 6) 현재 코드 조회 & Diff
            now_codes = await get_codes()  # 이미 6자리 정규화 보장
            added = sorted(set(now_codes) - set(prev_codes))
            removed = sorted(set(prev_codes) - set(now_codes))

            # 7) 스냅샷 저장
            await store.save(now_codes, source_ymd=source_ymd or "", etag=etag)

            logger.info(
                f"스냅샷 저장: {self.state_path} "
                f"(codes={len(now_codes)}, +{len(added)}, -{len(removed)})"
            )
            return SyncResult(True, source_ymd, etag, self.state_path, rows, added, removed)

        except Exception as e:
            logger.exception("SyncSnapshotUseCase 실행 중 예외")
            return SyncResult(False, None, None, None, 0, [], [], error=str(e))
        finally:
            if self.owns_client and self.client:
                await self.client.aclose()


# -------------------------
# helpers
# -------------------------
_YMD_RE = re.compile(r"(?<!\d)(20\d{6})(?!\d)")

def _guess_ymd_from_filename(p: Path) -> Optional[str]:
    """파일명에서 'YYYYMMDD' 패턴 추정."""
    m = _YMD_RE.search(p.stem)
    return m.group(1) if m else None

def _normalize_code_list(codes: list[str]) -> list[str]:
    """스냅샷에서 읽은 codes를 6자리 문자열로 정규화(방어적)."""
    return sorted({str(c).strip().zfill(6) for c in codes if c is not None})