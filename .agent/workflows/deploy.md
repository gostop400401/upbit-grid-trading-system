---
description: 코드 배포 (로컬 → GitHub → 서버)
---

# 배포 Workflow (개선판)

코드를 수정한 후 서버에 배포하는 전체 과정

**개선사항**: 검증된 명령, 원라이너 SSH, 명확한 결과 확인

---

## 1단계: 변경사항 확인
// turbo
```powershell
git status
```

수정된 파일 목록을 확인하세요.

---

## 2단계: Git 커밋 준비

```powershell
git add .
```

**확인**: 추가하지 말아야 할 파일이 있는지 확인
- ❌ `.env` (비밀키)
- ❌ `trading.db` (데이터베이스)
- ❌ `Dev_logs/` (개인 로그)

---

## 3단계: 커밋 메시지 작성

```powershell
# [메시지]를 실제 내용으로 변경하세요
git commit -m "[커밋 메시지를 입력하세요]"
```

**커밋 메시지 예시:**
- `Fix: 중복 매수 버그 수정`
- `Feature: 새로운 알림 추가`
- `Docs: README 업데이트`
- `Refactor: 코드 정리`

---

## 4단계: GitHub에 푸시
```powershell
git push
```

**확인**: "Everything up-to-date" 또는 성공 메시지

---

## 5단계: 서버에서 코드 업데이트
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "cd ~/upbit-grid-bot && git pull"
```

**확인**: 
- ✅ `Updating ...` → 코드 업데이트됨
- ✅ `Already up to date` → 이미 최신
- ❌ 에러 발생 → 수동 확인 필요

---

## 6단계: 봇 재시작
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "sudo systemctl restart upbit-grid-bot"
```

**재시작 대기**: 3초

---

## 7단계: 봇 프로세스 확인
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "ps aux | grep 'python.*main.py' | grep -v grep"
```

**확인사항:**
- ✅ 프로세스 실행 중 → 재시작 성공
- ❌ 출력 없음 → 봇 시작 실패 (8단계 진행)

---

## 8단계: 최근 로그 확인 (재시작 후 확인)
// turbo
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "sudo journalctl -u upbit-grid-bot -n 15 --no-pager"
```

**확인사항:**
- ✅ 에러 메시지 없음 → 정상
- ⚠️ Warning 있음 → 주의 깊게 확인
- ❌ Error/Exception → 롤백 고려

---

## 9단계: Discord 확인

Discord에서 확인:
1. 봇이 온라인 상태인지
2. `/상태` 명령어 정상 작동
3. 최근 알림 정상 수신

---

## ✅ 배포 성공 체크리스트

- [ ] Git push 성공
- [ ] 서버 코드 업데이트 확인
- [ ] 봇 재시작 완료
- [ ] 프로세스 실행 중
- [ ] 로그에 에러 없음
- [ ] Discord 봇 정상 작동

모두 체크되면 배포 완료! 🎉

---

## ❌ 배포 실패 시

### 봇이 시작 안됨
```powershell
# 상세 로그 확인
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "sudo journalctl -u upbit-grid-bot -n 50 --no-pager"
```

### 에러 로그 발견
1. 에러 메시지 복사
2. 로컬에서 코드 수정
3. 다시 1단계부터 시작

### 긴급 롤백 필요
```powershell
# 서버에서 이전 커밋으로 복구
ssh -i "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 "cd ~/upbit-grid-bot && git reset --hard HEAD~1 && sudo systemctl restart upbit-grid-bot"
```

---

## 📝 배포 후 권장사항

### 즉시 (5분 이내)
- Discord에서 기능 테스트
- 로그 모니터링

### 10분 후
- `/healthcheck` workflow 실행
- 활성 계약 확인

### 1시간 후
- 새 계약 생성 확인
- 알림 정상 동작 확인

---

## 완료!
배포가 성공적으로 완료되었습니다.
문제 발견 시 `/bug-analysis` workflow를 실행하세요.
