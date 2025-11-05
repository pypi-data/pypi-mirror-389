# krx300_hj3415/di.py
from pathlib import Path
from krx300_hj3415.core.usecases.sync_snapshot import SyncSnapshotUseCase
from krx300_hj3415.adapters.impls import (
    DefaultHttpClient, Downloader, Reader, Repo, HasherImpl, CodesStoreAdapter,
)

def build_sync_uc(state_path: Path) -> SyncSnapshotUseCase:
    httpc = DefaultHttpClient()
    return SyncSnapshotUseCase(
        state_store=CodesStoreAdapter(state_path),
        client=httpc,
        downloader=Downloader(),
        reader=Reader(),
        repo=Repo(),
        hasher=HasherImpl(),
        owns_client=True,
    )