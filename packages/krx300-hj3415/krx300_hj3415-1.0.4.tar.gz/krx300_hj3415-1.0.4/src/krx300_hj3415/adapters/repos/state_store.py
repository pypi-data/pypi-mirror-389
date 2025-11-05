# krx300_hj3415/adapters/repos/state_store.py

from __future__ import annotations
import json
import tempfile
import os
from pathlib import Path
from typing import Iterable, TypedDict
from datetime import datetime

class Snapshot(TypedDict, total=False):
    asof: str           # ISO 시각
    source_ymd: str     # 파일 기준일자(예: 20241102)
    etag: str           # 내용 해시(옵션)
    codes: list[str]    # 6자리 종목코드

class CodesStore:
    """아주 가벼운 파일 스냅샷 저장소(JSON)."""

    def __init__(self, path: Path):
        self.path = path

    async def load_snapshot(self) -> dict:
        """스냅샷 전체(JSON)를 dict로 반환."""
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    async def save(self, codes: Iterable[str], *, source_ymd: str, etag: str | None = None) -> None:
        codes6 = sorted({str(c).strip().replace(" ", "").zfill(6) for c in codes})
        payload: Snapshot = {
            "asof": datetime.now().isoformat(timespec="seconds"),
            "source_ymd": source_ymd,
            "codes": codes6,
        }
        if etag:
            payload["etag"] = etag

        tmp = Path(tempfile.gettempdir()) / f".{self.path.name}.tmp"
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # 원자적 치환