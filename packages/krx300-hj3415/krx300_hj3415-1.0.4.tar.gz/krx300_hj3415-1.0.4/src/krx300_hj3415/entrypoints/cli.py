# krx300_hj3415/entrypoints/cli.py

from __future__ import annotations

import json
from pathlib import Path
import typer
from loguru import logger

from krx300_hj3415.di import build_sync_uc

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="KRX300 스냅샷 동기화 CLI",
)

def _configure_logging(verbose: int, quiet: bool) -> None:
    # 기본: INFO. -v로 수준↑, --quiet로 수준↓
    level = "INFO"
    if quiet:
        level = "WARNING"
    if verbose >= 2:
        level = "DEBUG"
    elif verbose == 1 and not quiet:
        level = "INFO"

    logger.remove()
    logger.add(lambda msg: typer.echo(msg, nl=False), level=level)

# --- 추가: 공통 파일 저장 유틸 ---
def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    typer.secho(f"Wrote: {path}", fg=typer.colors.GREEN)

def _load_codes_from_snapshot(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("codes") or [])

@app.command(help="스냅샷 동기화 실행(다운로드→SQLite갱신→스냅샷 저장) 후 diff 출력")
def sync(
    state: Path = typer.Option(
        Path("./codes_snapshot.json"),
        "--state",
        "-s",
        help="스냅샷 JSON 파일 경로",
        dir_okay=False,
        readable=False,
    ),
    json_out: bool = typer.Option(
        False, "--json", help="머신친화적 JSON 출력(added/removed 포함)"
    ),
    out_json: Path | None = typer.Option(
        None, "--out-json", help="머신친화 JSON을 파일로 저장"
    ),
    out_codes: Path | None = typer.Option(
        None, "--out-codes", help="코드 목록만(한 줄당 1개) 파일로 저장"
    ),
    verbose: int = typer.Option(
        0, "--verbose", "-v", count=True, help="-v/-vv 로 로그 상세도 증가"
    ),
    quiet: bool = typer.Option(False, "--quiet", help="경고 이상만 출력"),
) -> None:
    _configure_logging(verbose, quiet)

    def _run():
        uc = build_sync_uc(state_path=state)
        return uc.run()

    import asyncio
    res = asyncio.run(_run())

    if not res.ok:
        typer.secho(f"ERROR: {res.error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    payload = {
        "ok": res.ok,
        "source_ymd": res.source_ymd,
        "etag": res.etag,
        "rows": res.rows,
        "added": res.added_codes,
        "removed": res.removed_codes,
        "snapshot_path": str(res.saved_json) if res.saved_json else None,
    }

    # --- 추가: 파일 저장 처리 ---
    if out_json is not None:
        _write_text(out_json, json.dumps(payload, ensure_ascii=False, indent=2))

    if out_codes is not None:
        # 최신 스냅샷 파일에서 코드 전체를 읽어 코드 파일 생성
        if not res.saved_json:
            typer.secho("스냅샷 파일 경로가 없습니다.", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        codes = _load_codes_from_snapshot(Path(res.saved_json))
        _write_text(out_codes, "\n".join(codes) + "\n")

    # 기존 출력
    if json_out:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        typer.secho(f"✓ 동기화 완료  rows={res.rows}", fg=typer.colors.GREEN)
        typer.echo(f"source_ymd: {res.source_ymd}  etag={res.etag}")
        typer.echo(f"snapshot : {res.saved_json}")
        typer.echo(
            f"추가(+{len(res.added_codes)}): {', '.join(res.added_codes) or '-'}"
        )
        typer.echo(
            f"삭제(-{len(res.removed_codes)}): {', '.join(res.removed_codes) or '-'}"
        )


@app.command(help="현재 스냅샷(JSON)의 코드 목록과 메타 정보 출력")
def show(
    state: Path = typer.Option(
        Path("./codes_snapshot.json"),
        "--state",
        "-s",
        help="스냅샷 JSON 파일 경로",
        dir_okay=False,
    ),
    json_out: bool = typer.Option(False, "--json", help="JSON 형태로 출력"),
    out_json: Path | None = typer.Option(
        None, "--out-json", help="현 스냅샷 내용을 JSON 파일로 저장"
    ),
    out_codes: Path | None = typer.Option(
        None, "--out-codes", help="코드 목록만(한 줄당 1개) 파일로 저장"
    ),
):
    from krx300_hj3415.adapters.repos.state_store import CodesStore

    async def _run():
        store = CodesStore(state)
        return await store.load_snapshot()

    import asyncio
    snap = asyncio.run(_run())

    if not snap:
        typer.secho("스냅샷이 비어있거나 파일이 없습니다.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    if out_json is not None:
        _write_text(out_json, json.dumps(snap, ensure_ascii=False, indent=2))
    if out_codes is not None:
        codes = list(snap.get("codes") or [])
        _write_text(out_codes, "\n".join(codes) + "\n")
        
    if json_out:
        typer.echo(json.dumps(snap, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"asof      : {snap.get('asof')}")
        typer.echo(f"source_ymd: {snap.get('source_ymd')}")
        typer.echo(f"etag      : {snap.get('etag')}")
        codes = snap.get("codes") or []
        typer.echo(f"codes({len(codes)}): {', '.join(codes[:20])}{' ...' if len(codes)>20 else ''}")


if __name__ == "__main__":
    app()