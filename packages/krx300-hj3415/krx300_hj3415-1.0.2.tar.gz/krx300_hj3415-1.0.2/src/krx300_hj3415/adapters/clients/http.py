# krx300_hj3415/adapters/clients/http.py
import httpx
from krx300_hj3415.adapters.constants import USER_AGENT

def default_headers() -> dict:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }

def new_client() -> httpx.AsyncClient:
    # 필요 시 프록시/timeout 조정
    return httpx.AsyncClient(
        timeout=httpx.Timeout(15.0, connect=10.0),
        headers=default_headers(),
        follow_redirects=True,
        http2=True,
    )