---
description: 버그 분석 (DB 다운로드 → 로컬 분석)
---

# 버그 분석 Workflow (개선판)

버그 발생 시 효율적으로 원인을 파악하는 과정

**핵심**: 서버 데이터를 로컬로 가져와서 분석

---

## 1단계: Dev_logs 폴더 확인
```powershell
if (-not (Test-Path "Dev_logs")) { 
    New-Item -ItemType Directory -Path "Dev_logs"
    Write-Host "✅ Dev_logs 폴더 생성 완료"
}
```

---

## 2단계: 데이터베이스 다운로드 ⭐ 최우선
// turbo
```powershell
$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:~/upbit-grid-bot/trading.db "Dev_logs/${date}_db_trading.db"
Write-Host "✅ DB 다운로드 완료: Dev_logs/${date}_db_trading.db"
```

---

## 3단계: 최근 계약 확인 (최근 10개)
```powershell
$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$dbPath = Get-ChildItem "Dev_logs" -Filter "*_db_trading.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

python -c "import sqlite3; conn = sqlite3.connect('$($dbPath.FullName)'); cursor = conn.cursor(); cursor.execute('SELECT id, buy_price, buy_amount, status, created_at FROM contracts ORDER BY id DESC LIMIT 10'); print('최근 계약 10개:'); print('-' * 80); [print(f'ID:{r[0]:3d} | Price:{r[1]:7.1f} | Amt:{r[2]:5.1f} | {r[3]:8s} | {r[4]}') for r in cursor.fetchall()]; conn.close()"
```

---

## 4단계: 특정 가격대 중복 확인 (선택)

문제 가격을 찾았다면:
```powershell
# [가격]을 실제 숫자로 변경하세요 (예: 1488.0)
$dbPath = Get-ChildItem "Dev_logs" -Filter "*_db_trading.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

python -c "import sqlite3; conn = sqlite3.connect('$($dbPath.FullName)'); cursor = conn.cursor(); cursor.execute('SELECT id, buy_price, buy_amount, created_at, buy_order_uuid FROM contracts WHERE buy_price = [가격] ORDER BY created_at'); [print(f'ID:{r[0]} Time:{r[3]} UUID:{r[4][:8]}...') for r in cursor.fetchall()]; conn.close()"
```

---

## 5단계: 로그 다운로드 (필요시)

### 시간대를 알고 있을 때:
```powershell
# UTC 시간으로 변경 필요! (한국 시간 - 9시간)
# 예: 한국 10:03 → UTC 01:03

$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile = "Dev_logs/${date}_log_debug.txt"

# PowerShell에서 직접 실행하지 말고, 아래 bash 명령을 복사해서 SSH 터미널에서 실행:
```

```bash
# SSH 접속 후 실행:
sudo journalctl -u upbit-grid-bot --since "YYYY-MM-DD HH:MM:SS" --until "YYYY-MM-DD HH:MM:SS" > /tmp/debug_log.txt
```

```powershell
# 그 다음 로컬로 다운로드:
$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:/tmp/debug_log.txt "Dev_logs/${date}_log_debug.txt"
```

---

## 6단계: 로컬에서 로그 분석

### 에러 검색:
```powershell
$logFile = Get-ChildItem "Dev_logs" -Filter "*_log_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Select-String -Path $logFile.FullName -Pattern "ERROR|Exception|Failed|Error" | Select-Object -First 20
```

### 특정 키워드 검색:
```powershell
$logFile = Get-ChildItem "Dev_logs" -Filter "*_log_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
# [키워드]를 실제 검색어로 변경
Select-String -Path $logFile.FullName -Pattern "[키워드]" | Select-Object -First 20
```

또는 VSCode에서:
```powershell
$logFile = Get-ChildItem "Dev_logs" -Filter "*_log_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
code $logFile.FullName
```
(Ctrl+F로 검색)

---

## 7단계: 코드 분석

VSCode에서 관련 함수 검색:
- `Ctrl+Shift+F` - 전체 검색
- `Ctrl+P` - 파일 빠르게 열기
- `F12` - 정의로 이동
- `Shift+F12` - 모든 참조 찾기

---

## 8단계: 버그 리포트 작성
```powershell
$date = Get-Date -Format "yyyy-MM-dd"
$bugName = Read-Host "버그 이름을 입력하세요 (예: race_condition)"
code "Dev_logs/${date}_bugfix_${bugName}.md"
```

---

## 📝 버그 리포트 템플릿

새 파일에 다음 내용을 작성하세요:

```markdown
# 버그 수정: [버그명]

**날짜**: YYYY-MM-DD
**발견**: [어떻게 발견했는지]

## 증상
- 

## 원인
- 

## 수정 방법
- 

## 테스트
- [ ] 로컬 테스트
- [ ] 서버 배포
- [ ] 모니터링

## 관련 파일
- Dev_logs/YYYY-MM-DD_db_trading.db
- Dev_logs/YYYY-MM-DD_log_debug.txt
```

---

## 완료!
분석 완료. 수정 후 `/deploy` workflow로 배포하세요.
