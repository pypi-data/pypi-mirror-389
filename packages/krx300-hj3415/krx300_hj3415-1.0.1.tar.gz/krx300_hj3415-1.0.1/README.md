# 로컬 개발 설치
pip install -e .

# 동기화 실행 (기본: ./codes_snapshot.json)
krx300 sync

# JSON 출력으로 받기
krx300 sync --json

# 스냅샷 보기
krx300 show -s ./codes_snapshot.json

# 로그 상세
krx300 sync -v
krx300 sync -vv
krx300 sync --quiet