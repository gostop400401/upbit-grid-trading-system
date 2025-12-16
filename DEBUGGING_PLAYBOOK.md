# 🔧 클라우드 서버 디버깅 플레이북

**목적**: 클라우드 서버의 버그를 빠르고 효율적으로 분석하는 방법론

**작성일**: 2025-12-16  
**기반 사례**: 중복 매수 버그 분석 (2025-12-16)

---

## ⚠️ 피해야 할 실수들 (오늘의 시행착오)

### ❌ 하지 말아야 할 것들

1. **SSH 터미널에서 긴 로그 직접 보기**
   - `journalctl` 출력이 터미널에서 깨짐
   - `grep` 파이프가 제대로 작동 안함
   - 스크롤이 어렵고 복사/붙여넣기도 불편
   - **결과**: 시간 낭비 ⏰

2. **로그를 실시간으로 분석하려고 시도**
   - 너무 많은 로그가 빠르게 지나감
   - 중요한 부분을 놓침
   - **결과**: 정확한 분석 불가능 ❌

3. **서버에서 복잡한 명령어 체이닝**
   - `grep | awk | sed` 같은 복잡한 파이프라인
   - 문법 에러가 나도 디버깅 어려움
   - **결과**: 좌절감 증가 😫

---

## ✅ 베스트 프랙티스 (검증된 효율적인 방법)

### 📋 전체 워크플로우

```
1단계: 증상 확인 (Discord/사용자 보고)
   ↓
2단계: 데이터베이스 다운로드 & 로컬 분석 ⭐
   ↓
3단계: 관련 시간대 로그 다운로드 (필요시)
   ↓
4단계: 코드 분석 (Race Condition 등)
   ↓
5단계: 수정 & 배포
```

---

## 🎯 1단계: 증상 확인

### Discord 알림 또는 사용자 보고
- 스크린샷 확인
- 계약 ID, 가격, 시간 기록
- 재현 가능한지 확인

**예시 (오늘)**:
```
- 계약 ID: 16, 17
- 가격: 1488.0 KRW (동일)
- 시간: 10:03:43-44 (1초 차이)
- 증상: 중복 매수
```

---

## 🎯 2단계: 데이터베이스 다운로드 & 분석 ⭐⭐⭐

### 🔥 **가장 효율적인 방법!**

#### 2.1 데이터베이스 다운로드
```powershell
# SCP로 데이터베이스 즉시 다운로드 (Dev_logs 폴더에 저장)
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:~/upbit-grid-bot/trading.db "c:\Users\MINIMON\Desktop\AI작업\6.upbit usdt trading\Dev_logs\trading_db_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

**장점**:
- ✅ 3초 안에 완료 (32KB 파일)
- ✅ 로컬에서 자유롭게 분석 가능
- ✅ Python, SQLite 브라우저 등 다양한 도구 사용 가능
- ✅ 재현 불가능한 버그도 데이터 보존

#### 2.2 로컬에서 Python으로 분석
```powershell
# 특정 계약 ID 분석
python -c "import sqlite3; conn = sqlite3.connect('Dev_logs/trading_db_20251216.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(contracts)'); columns = [col[1] for col in cursor.fetchall()]; cursor.execute('SELECT * FROM contracts WHERE id BETWEEN 14 AND 19'); rows = cursor.fetchall(); [print(f'\nContract {row[0]}:') or [print(f'  {col}: {val}') for col, val in zip(columns, row)] for row in rows]; conn.close()"

# 특정 가격대 주문 검색
python -c "import sqlite3; conn = sqlite3.connect('Dev_logs/trading_db_20251216.db'); cursor = conn.cursor(); cursor.execute('SELECT id, buy_price, buy_amount, status, created_at FROM contracts WHERE buy_price = 1488.0'); [print(row) for row in cursor.fetchall()]; conn.close()"

# 시간대별 주문 분석
python -c "import sqlite3; conn = sqlite3.connect('Dev_logs/trading_db_20251216.db'); cursor = conn.cursor(); cursor.execute(\"SELECT id, buy_price, created_at FROM contracts WHERE created_at LIKE '2025-12-16 01:03%' ORDER BY created_at\"); [print(row) for row in cursor.fetchall()]; conn.close()"
```

**결과 예시**:
```
Contract 16:
  id: 16
  buy_price: 1488.0
  created_at: 2025-12-16 01:03:43  ← 1초 차이 발견!
  buy_order_uuid: 7caea73f-...

Contract 17:
  id: 17
  buy_price: 1488.0
  created_at: 2025-12-16 01:03:44  ← 중복 확인!
  buy_order_uuid: 364d029f-...
```

---

## 🎯 3단계: 로그 다운로드 (선택사항)

### 3.1 서버에서 로그 파일로 저장
```bash
# SSH 접속 후
sudo journalctl -u upbit-grid-bot --since "2025-12-16 01:00:00" --until "2025-12-16 01:10:00" > /tmp/debug_log.txt
```

### 3.2 로컬로 다운로드
```powershell
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:/tmp/debug_log.txt "c:\Users\MINIMON\Desktop\AI작업\6.upbit usdt trading\Dev_logs\debug_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
```

### 3.3 로컬에서 분석
```powershell
# PowerShell에서 로그 검색
Select-String -Path "Dev_logs\debug_log_*.txt" -Pattern "매수|buy|Order|Error" | Select-Object -First 20

# 또는 VSCode에서 열어서 검색 (Ctrl+F)
code "Dev_logs\debug_log_*.txt"
```

---

## 🎯 4단계: 코드 분석

### 4.1 의심 함수 찾기
```powershell
# 특정 함수 호출 찾기
grep -rn "_fill_empty_grids" modules/

# Lock 사용 여부 확인
grep -rn "async with.*_lock" modules/

# 주문 실행 함수 찾기
grep -rn "buy_limit_order" modules/
```

### 4.2 VSCode로 코드 분석
- `Ctrl+P` → 파일 빠르게 열기
- `Ctrl+Shift+F` → 전체 검색
- `F12` → 정의로 이동
- `Shift+F12` → 모든 참조 찾기

### 4.3 Race Condition 체크리스트
- [ ] Lock 정의되어 있는가?
- [ ] Lock이 실제로 사용되는가?
- [ ] 여러 비동기 태스크가 동시 실행 가능한가?
- [ ] 중복 체크가 원자적(atomic)으로 실행되는가?

---

## 🎯 5단계: 수정 & 배포

### 5.1 코드 수정
```python
# 예시: Lock 추가
async def critical_function(self):
    async with self._lock:  # 🔒 문지기 패턴
        # 중요한 작업
        pass
```

### 5.2 Git 커밋 & 푸시
```powershell
git add .
git commit -m "🔒 Fix: [버그 설명] - [해결 방법]"
git push
```

### 5.3 서버 배포 (한 줄 명령어)
```bash
# SSH 접속 후
cd ~/upbit-grid-bot && git pull && sudo systemctl restart upbit-grid-bot && sudo systemctl status upbit-grid-bot --no-pager
```

### 5.4 배포 확인
```bash
# 프로세스 확인
ps aux | grep "python.*main.py" | grep -v grep

# 최근 로그 확인
sudo journalctl -u upbit-grid-bot --since "1 minute ago" --no-pager | tail -20
```

---

## 📊 타임라인 비교

### ❌ 오늘의 시행착오 방식 (총 40분)
```
1. SSH 터미널에서 journalctl 시도 (10분)
   → 출력 깨짐, grep 안됨
   
2. 다양한 grep 필터 시도 (10분)
   → 제대로 안됨
   
3. 로그 파일 저장 시도 (5분)
   → 다운로드 안됨
   
4. 데이터베이스 다운로드 (3분)
   → 성공! ✅
   
5. 로컬에서 분석 (5분)
   → 원인 파악 ✅
   
6. 코드 분석 및 수정 (7분)
   → 완료 ✅
```

### ✅ 베스트 프랙티스 방식 (총 15분 예상)
```
1. 데이터베이스 즉시 다운로드 (1분)
   → Dev_logs에 저장 ✅
   
2. 로컬에서 Python 분석 (3분)
   → 계약 ID, 시간, UUID 확인 ✅
   
3. 코드에서 대상 함수 검색 (2분)
   → _fill_empty_grids 발견 ✅
   
4. Lock 패턴 적용 (5분)
   → 수정 완료 ✅
   
5. 배포 및 확인 (4분)
   → 완료 ✅
```

**시간 절약**: 25분 (약 60% 단축!) ⏰✨

---

## 🛠️ 유용한 명령어 모음

### SSH 연결
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180
```

### 데이터베이스 다운로드 (즉시 실행)
```powershell
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:~/upbit-grid-bot/trading.db "c:\Users\MINIMON\Desktop\AI작업\6.upbit usdt trading\Dev_logs\trading_db_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### 서버 상태 한눈에 보기
```bash
echo "=== 봇 프로세스 ===" && \
ps aux | grep "python.*main.py" | grep -v grep && \
echo "" && \
echo "=== 시스템 리소스 ===" && \
top -bn1 | grep "python" | head -3 && \
echo "" && \
echo "=== 최근 로그 (5줄) ===" && \
sudo journalctl -u upbit-grid-bot -n 5 --no-pager
```

### 배포 원라이너
```bash
cd ~/upbit-grid-bot && git pull && sudo systemctl restart upbit-grid-bot && sleep 3 && sudo journalctl -u upbit-grid-bot -n 10 --no-pager
```

---

## 📝 디버깅 체크리스트

### 초기 조사
- [ ] 사용자 보고/Discord 스크린샷 확인
- [ ] 계약 ID, 가격, 시간 기록
- [ ] **즉시 데이터베이스 다운로드** ⭐

### 데이터 분석
- [ ] 로컬에서 DB 열기
- [ ] 문제 계약 ID 상세 조회
- [ ] 시간대별 패턴 확인
- [ ] UUID 중복 여부 확인

### 코드 분석
- [ ] 관련 함수 찾기
- [ ] Lock 사용 확인
- [ ] Race Condition 가능성 확인
- [ ] 동시성 제어 확인

### 수정 및 배포
- [ ] 코드 수정
- [ ] 로컬 테스트 (선택)
- [ ] Git 커밋 & 푸시
- [ ] 서버 배포
- [ ] 로그 모니터링

---

## 💡 핵심 원칙

1. **데이터부터 확보하라** 📦
   - 서버 로그는 휘발성이지만 데이터베이스는 영구적
   - 분석 전에 먼저 다운로드!

2. **로컬에서 분석하라** 💻
   - 서버 터미널은 제한적
   - 로컬 환경이 훨씬 강력함

3. **간단하게 유지하라** ✨
   - 복잡한 명령어 체이닝보다 단순한 파일 다운로드
   - Python 한 줄이 bash 10줄보다 명확함

4. **재현 가능하게 보존하라** 📁
   - Dev_logs에 모든 데이터 저장
   - 타임스탬프 포함된 파일명 사용

---

## 🎓 배운 교훈 (2025-12-16)

### 시행착오에서 배운 것
1. SSH 터미널의 한계를 알게 됨
2. SCP의 강력함을 재발견
3. 로컬 환경의 중요성 인식
4. "빠르게 데이터 확보 → 천천히 분석"이 효율적

### 다음에 바로 적용할 것
1. **첫 번째 액션**: DB 다운로드
2. **두 번째 액션**: 로컬 Python 분석
3. **세 번째 액션**: 코드 검색 및 수정
4. 서버 로그는 최후 수단

---

## 🔗 관련 문서

- `MAINTENANCE.md` - 일반적인 유지보수 가이드
- `BUGFIX_DuplicateOrder.md` - 오늘 버그 수정 상세 내역
- `.gitignore` - Dev_logs는 git에서 제외됨 (개인 분석용)

---

**마지막 업데이트**: 2025-12-16  
**다음 개선**: 이 플레이북을 따라 실제로 버그 수정 후 보완
