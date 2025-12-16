---
description: 서버 및 봇 상태 종합 점검
---

# 헬스체크 Workflow (개선판)

정기적으로 서버와 봇의 상태를 점검하는 과정

**개선사항**: 검증된 원라이너 SSH 명령만 사용

---

## 1단계: 봇 프로세스 확인
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "ps aux | grep 'python.*main.py' | grep -v grep"
```

**확인사항:**
- ✅ ubuntu XXX ... /home/ubuntu/upbit-grid-bot/venv/bin/python main.py
- ❌ 출력 없음 → 봇이 중지됨

---

## 2단계: 디스크 사용량 확인
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "df -h ~"
```

**확인사항:**
- ✅ Use% < 80% 정상
- ⚠️ Use% > 80% 주의
- ❌ Use% > 95% 긴급

---

## 3단계: 데이터베이스 크기 및 최근 수정 시간
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "ls -lh ~/upbit-grid-bot/trading.db"
```

**확인사항:**
- ✅ 최근 10분 이내 수정 → 정상 동작
- ⚠️ 1시간 이상 수정 없음 → 확인 필요

---

## 4단계: 최근 로그 확인 (최근 10줄)
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "sudo journalctl -u upbit-grid-bot -n 10 --no-pager"
```

**확인사항:**
- 에러 메시지 없는지 확인
- 정상적인 로그 출력 확인

---

## 5단계: 활성 계약 수 확인

### 방법 A: DB 다운로드 후 로컬 확인 (권장) ⭐
```powershell
# DB 다운로드
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
scp -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180:~/upbit-grid-bot/trading.db "c:\Users\MINIMON\Desktop\AI작업\6.upbit usdt trading\Dev_logs\${timestamp}_db_temp.db"

# 로컬에서 확인
python -c "import sqlite3; conn = sqlite3.connect('Dev_logs/${timestamp}_db_temp.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM contracts WHERE status=\"ACTIVE\"'); print(f'Active contracts: {c.fetchone()[0]}'); conn.close()"
```

### 방법 B: Discord에서 확인 (가장 간단)
Discord에서 `/상태` 명령어로 활성 계약 확인

---

## 6단계: 서버 재부팅 필요 여부 확인
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "if [ -f /var/run/reboot-required ]; then echo 'Reboot required'; else echo 'No reboot needed'; fi"
```

---

## 📊 종합 평가 체크리스트

수동으로 확인하세요:

- [ ] 봇 프로세스 실행 중
- [ ] 디스크 여유 공간 충분 (< 80%)
- [ ] 데이터베이스 최근 업데이트 확인
- [ ] 로그에 에러 없음
- [ ] 활성 계약 확인 (Discord 또는 DB)
- [ ] 재부팅 불필요

---

## ✅ 모두 정상이면

다음 헬스체크까지 대기하세요.
- 정기 점검: 주 1-2회
- 이상 징후 발견 시: 즉시

---

## ❌ 문제 발견 시

### 봇 프로세스 중지됨
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "cd ~/upbit-grid-bot && sudo systemctl restart upbit-grid-bot"
```

### 에러 로그 발견
→ `/bug-analysis` workflow 실행

### 디스크 거의 가득 참
→ 로그 정리 필요 (별도 workflow)

---

## 완료!
모든 상태 확인 완료. 문제 없으면 정상 운영 계속.
