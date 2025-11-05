

## **🧭 기본 구조**

```
krx300 [COMMAND] [OPTIONS]
```

### **주요 명령어**

|**명령어**|**설명**|
|---|---|
|sync|최신 KRX300 구성요소(코드 목록 등)를 다운로드하고 스냅샷 파일을 갱신|
|show|기존 스냅샷 파일(codes_snapshot.json) 내용을 조회 또는 내보내기|

---

## 1.**sync 명령어 — 스냅샷 동기화**

> “KRX300 코드 목록을 새로 다운로드하고 JSON 스냅샷을 갱신합니다.”

### **✅ 기본 사용**

```
krx300 sync
```

- 현재 디렉터리의 ./codes_snapshot.json을 자동 생성 또는 갱신합니다.
    
- 콘솔에 다음과 같이 표시됩니다:
    

```
✓ 동기화 완료  rows=300
source_ymd: 20251105  etag: E123456
snapshot : codes_snapshot.json
추가(+3): 001234, 002345, 004321
삭제(-1): 003456
```

---

### **✅ 출력 JSON 보기**

```
krx300 sync --json
```

- JSON 형식으로 결과를 출력:
    

```
{
  "ok": true,
  "source_ymd": "20251105",
  "etag": "E123456",
  "rows": 300,
  "added": ["001234"],
  "removed": [],
  "snapshot_path": "codes_snapshot.json"
}
```

---

### **✅ 파일로 결과 저장**

```
krx300 sync --out-json ./result.json --out-codes ./codes.txt
```

- result.json → 동기화 결과 요약(JSON)
    
- codes.txt → 코드 목록만 한 줄씩 저장
    

```
005930
000660
035420
...
```

→ 이 파일은 **scraper2-hj3415**에 바로 사용할 수 있습니다:

```
scraper2 ingest many --file ./codes.txt --save
```

---

### **✅ 기타 유용한 옵션**

|**옵션**|**설명**|**기본값**|
|---|---|---|
|--state, -s|스냅샷 JSON 파일 경로|./codes_snapshot.json|
|--json|콘솔 출력 대신 JSON 형식 출력|False|
|--out-json PATH|결과를 JSON 파일로 저장|None|
|--out-codes PATH|코드 목록을 텍스트 파일로 저장|None|
|-v, -vv|로그 상세도 증가|-|
|--quiet|경고 이상만 출력|False|

---

## **2.show 명령어 — 스냅샷 내용 보기**

> 기존에 저장된 codes_snapshot.json 내용을 출력하거나 내보냅니다.

### **✅ 기본 사용**

```
krx300 show
```

출력 예시:

```
asof      : 2025-11-05
source_ymd: 20251104
etag      : E123456
codes(300): 005930, 000660, 035420, 051910, ...
```

---

### **✅ JSON으로 보기**

```
krx300 show --json
```

- 스냅샷 내용을 JSON으로 표시.
    

---

### **✅ 파일로 내보내기**

```
krx300 show --out-codes ./codes.txt
```

- 코드 목록만 추출해서 텍스트 파일로 저장.
    
    (scraper2에서 --file로 바로 사용 가능)
    

---

## **전체 예시 흐름 (통합 시나리오)**

```
# 1️⃣ KRX300 스냅샷 동기화 및 코드 목록 생성
krx300 sync --out-codes ./codes.txt

# 2️⃣ Scraper2로 코드 목록을 사용해 실제 수집 및 MongoDB 저장
scraper2 ingest many --file ./codes.txt --pages c103 c104 --save
```
