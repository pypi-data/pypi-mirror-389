# krx300_hj3415/adapters/repos/hashutil.py

from __future__ import annotations
from pathlib import Path
import hashlib

def file_sha256(p: Path) -> str:
    # 주어진 파일 p의 **SHA-256 해시값(고유 지문)**을 계산해서 문자열로 반환
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()