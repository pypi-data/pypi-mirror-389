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

    if json_out:
        payload = {
            "ok": res.ok,
            "source_ymd": res.source_ymd,
            "etag": res.etag,
            "rows": res.rows,
            "added": res.added_codes,
            "removed": res.removed_codes,
            "snapshot_path": str(res.saved_json) if res.saved_json else None,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        typer.secho(f"✓ 동기화 완료  rows={res.rows}", fg=typer.colors.GREEN)
        typer.echo(f"source_ymd: {res.source_ymd}  etag={res.etag}")
        typer.echo(f"snapshot : {res.saved_json}")
        typer.echo(f"추가(+{len(res.added_codes)}): {', '.join(res.added_codes) or '-'}")
        typer.echo(f"삭제(-{len(res.removed_codes)}): {', '.join(res.removed_codes) or '-'}")


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