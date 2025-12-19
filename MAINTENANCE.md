# Upbit Grid Trading Bot - 유지보수 가이드

이 문서는 프로그램 수정 후 배포, 서버 관리, 모니터링 등 모든 유지보수 작업을 안내합니다.

---

## 📋 목차
1. [코드 수정 후 GitHub 업로드](#1-코드-수정-후-github-업로드)
2. [서버 접속 방법](#2-서버-접속-방법)
3. [서버에 최신 코드 적용](#3-서버에-최신-코드-적용)
4. [서비스 관리 (시작/중지/재시작)](#4-서비스-관리)
5. [로그 확인 및 모니터링](#5-로그-확인-및-모니터링)
6. [설정 변경 (.env 파일 수정)](#6-설정-변경)
7. [문제 해결 (Troubleshooting)](#7-문제-해결)
8. [빠른 명령어 참조](#8-빠른-명령어-참조)

---

## 1. 코드 수정 후 GitHub 업로드

### 로컬에서 코드 수정 후 GitHub에 푸시하기

```powershell
# 프로젝트 디렉토리로 이동
cd "C:\Users\MINIMON\Desktop\AI Works\6.upbit usdt trading"

# 변경된 파일 확인
git status

# 모든 변경사항 스테이징
git add .

# 커밋 (메시지는 변경 내용에 맞게 수정)
git commit -m "수정 내용 설명"

# GitHub에 푸시
git push
```

**GitHub 리포지토리 URL:**
```
https://github.com/gostop400401/upbit-grid-trading-system
```

### 특정 파일만 업로드하기
```powershell
git add modules/trading_manager.py
git commit -m "Fix trading logic"
git push
```

---

## 2. 서버 접속 방법

### SSH 접속 명령어
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI Works\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180
```

### PowerShell 관리 스크립트 사용
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 connect
```

**서버 정보:**
- IP: `168.138.214.180`
- User: `ubuntu`
- Bot Directory: `~/upbit-grid-bot`

---

## 3. 서버에 최신 코드 적용

### 방법 1: 로컬에서 한 번에 실행 (권장)
```powershell
# PowerShell에서
powershell -ExecutionPolicy Bypass -File manage_server.ps1 update
```

이 명령어는 자동으로:
1. 서버 접속
2. `git pull` 실행
3. 봇 재시작

### 방법 2: 서버에 접속해서 수동 실행
```bash
# 서버 접속 후
cd ~/upbit-grid-bot
git pull
sudo systemctl restart upbit-grid-bot
```

### 방법 3: SSH 원격 명령어
```powershell
ssh -i "C:\Users\MINIMON\Desktop\AI Works\5.bn funding fee\ssh-key-2025-03-01.key" ubuntu@168.138.214.180 'cd upbit-grid-bot; git pull; sudo systemctl restart upbit-grid-bot'
```

---

## 4. 서비스 관리

### 4.1 봇 시작
```bash
sudo systemctl start upbit-grid-bot
```

또는 로컬에서:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 start
```

### 4.2 봇 중지
```bash
sudo systemctl stop upbit-grid-bot
```

또는:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 stop
```

### 4.3 봇 재시작
```bash
sudo systemctl restart upbit-grid-bot
```

또는:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 restart
```

### 4.4 봇 상태 확인
```bash
sudo systemctl status upbit-grid-bot
```

또는:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 status
```

**상태 해석:**
- `Active: active (running)` (초록색) → 정상 실행 중 ✅
- `Active: inactive (dead)` → 중지됨
- `Active: failed` (빨간색) → 에러 발생 ❌

### 4.5 부팅 시 자동 시작 설정
```bash
sudo systemctl enable upbit-grid-bot  # 자동 시작 활성화
sudo systemctl disable upbit-grid-bot # 자동 시작 비활성화
```

---

## 5. 로그 확인 및 모니터링

### 5.1 실시간 로그 보기 (가장 많이 사용)
```bash
sudo journalctl -u upbit-grid-bot -f
```

**나가기:** `Ctrl + C`

또는 로컬에서:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 logs
```

### 5.2 최근 로그 확인 (최근 50줄)
```bash
sudo journalctl -u upbit-grid-bot -n 50 --no-pager
```

### 5.3 특정 시간 이후 로그 보기
```bash
# 최근 10분
sudo journalctl -u upbit-grid-bot --since "10 minutes ago" --no-pager

# 최근 1시간
sudo journalctl -u upbit-grid-bot --since "1 hour ago" --no-pager

# 오늘 로그
sudo journalctl -u upbit-grid-bot --since today --no-pager
```

### 5.4 에러만 필터링
```bash
sudo journalctl -u upbit-grid-bot -p err --no-pager
```

### 5.5 프로세스 확인
```bash
# 봇이 실행 중인지 확인
ps aux | grep python | grep main.py

# CPU/메모리 사용량 확인
top -p $(pgrep -f main.py)
```

---

## 6. 설정 변경

### 6.1 .env 파일 수정
```bash
cd ~/upbit-grid-bot
nano .env
```

**저장 및 종료:**
- `Ctrl + O` → `Enter` (저장)
- `Ctrl + X` (종료)

또는 로컬에서:
```powershell
powershell -ExecutionPolicy Bypass -File manage_server.ps1 edit-env
```

### 6.2 설정 적용 (재시작 필수)
```bash
sudo systemctl restart upbit-grid-bot
```

### 6.3 설정 파일 내용 확인 (비밀번호는 가려짐)
```bash
cat .env
```

---

## 7. 문제 해결

### 7.1 봇이 시작되지 않을 때

**1단계: 로그 확인**
```bash
sudo journalctl -u upbit-grid-bot -n 50 --no-pager
```

**2단계: 상태 확인**
```bash
sudo systemctl status upbit-grid-bot
```

**3단계: 수동 실행으로 에러 확인**
```bash
cd ~/upbit-grid-bot
source venv/bin/activate
python main.py
```
(에러 메시지가 바로 보임. 종료: `Ctrl + C`)

**4단계: 재시작**
```bash
sudo systemctl restart upbit-grid-bot
```

### 7.2 자주 발생하는 에러

#### ValueError: invalid literal for int()
- **원인:** `.env` 파일의 숫자 값이 잘못됨 (예: `YOUR_CHANNEL_ID`)
- **해결:** `.env` 파일 수정 후 재시작

#### discord.errors.LoginFailure
- **원인:** Discord Bot Token이 잘못됨
- **해결:** `.env`의 `DISCORD_TOKEN` 확인

#### Upbit API Error
- **원인:** API 키가 잘못되었거나 IP 화이트리스트 미등록
- **해결:** 
  1. `.env`의 Upbit 키 확인
  2. Upbit API 관리 페이지에서 서버 IP(`168.138.214.180`) 화이트리스트 등록

#### Database Locked
- **원인:** 동시에 여러 프로세스가 DB 접근
- **해결:** 봇 중지 후 재시작
  ```bash
  sudo systemctl stop upbit-grid-bot
  sleep 2
  sudo systemctl start upbit-grid-bot
  ```

### 7.3 봇 완전 초기화 (데이터베이스 삭제)
```bash
cd ~/upbit-grid-bot
sudo systemctl stop upbit-grid-bot
rm trading.db  # 주의: 모든 거래 기록 삭제됨!
sudo systemctl start upbit-grid-bot
```

### 7.4 서비스 파일 수정 (고급)
```bash
sudo nano /etc/systemd/system/upbit-grid-bot.service
# 수정 후
sudo systemctl daemon-reload
sudo systemctl restart upbit-grid-bot
```

---

## 8. 빠른 명령어 참조

### 로컬 (PowerShell)

| 작업 | 명령어 |
|------|--------|
| 서버 접속 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 connect` |
| 코드 업데이트 & 재시작 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 update` |
| 봇 시작 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 start` |
| 봇 중지 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 stop` |
| 봇 재시작 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 restart` |
| 상태 확인 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 status` |
| 실시간 로그 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 logs` |
| .env 수정 | `powershell -ExecutionPolicy Bypass -File manage_server.ps1 edit-env` |

### GitHub 작업

| 작업 | 명령어 |
|------|--------|
| 변경사항 확인 | `git status` |
| 모든 파일 추가 | `git add .` |
| 커밋 | `git commit -m "메시지"` |
| 푸시 | `git push` |

### 서버 (SSH 접속 후)

| 작업 | 명령어 |
|------|--------|
| 봇 디렉토리 이동 | `cd ~/upbit-grid-bot` |
| 최신 코드 받기 | `git pull` |
| 봇 시작 | `sudo systemctl start upbit-grid-bot` |
| 봇 중지 | `sudo systemctl stop upbit-grid-bot` |
| 봇 재시작 | `sudo systemctl restart upbit-grid-bot` |
| 상태 확인 | `sudo systemctl status upbit-grid-bot` |
| 실시간 로그 | `sudo journalctl -u upbit-grid-bot -f` |
| 최근 로그 | `sudo journalctl -u upbit-grid-bot -n 50 --no-pager` |
| .env 수정 | `nano .env` |
| 프로세스 확인 | `ps aux \| grep python \| grep main.py` |

---

## 📝 일반적인 작업 흐름

### 코드 수정 후 서버 배포 (전체 과정)

```powershell
# 1. 로컬에서 코드 수정 후 GitHub 업로드
cd "C:\Users\MINIMON\Desktop\AI Works\6.upbit usdt trading"
git add .
git commit -m "수정 내용"
git push

# 2. 서버 업데이트 및 재시작 (한 줄로!)
powershell -ExecutionPolicy Bypass -File manage_server.ps1 update

# 3. 로그 확인
powershell -ExecutionPolicy Bypass -File manage_server.ps1 logs
```

끝! 🎉

---

## ⚠️ 주의사항

1. **`.env` 파일은 절대 GitHub에 올리지 마세요!** (이미 `.gitignore`에 포함됨)
2. **서비스 중지 없이 코드 수정하면 반영 안 됩니다.** 반드시 재시작하세요.
3. **데이터베이스(`trading.db`) 삭제는 신중히!** 모든 거래 기록이 사라집니다.
4. **Upbit API IP 화이트리스트** 잊지 마세요. (서버 IP: `168.138.214.180`)

---

## 📞 지원

Discord에서 봇 테스트:
- `!시작` - 그리드 트레이딩 설정
- `!상태` - 현재 상태 확인
- `!종료` - 트레이딩 중단
- `!리포트` - 최근 거래 내역

**GitHub:** https://github.com/gostop400401/upbit-grid-trading-system
