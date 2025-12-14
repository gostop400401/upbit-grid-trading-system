# Upbit Grid Trading Bot

업비트 그리드 트레이딩 시스템 - Discord Bot 기반 자동 매매 시스템

## 📋 주요 기능

- **그리드 트레이딩**: 지정한 가격 범위 내에서 자동으로 매수/매도 반복
- **Discord 알림**: 모든 거래 체결 시 실시간 알림 (수익금 포함)
- **자금 검증**: 시작 전 필요 자금과 보유 자금 비교하여 안전 확인
- **실시간 모니터링**: 현재 상태, 미실현 손익, 거래 내역 조회
- **자동 복구**: 서버 재부팅 시에도 자동으로 재시작

## 🚀 빠른 시작 (클라우드 서버)

### 1. 서버 접속
```powershell
.\manage_server.ps1 connect
```

### 2. .env 파일 설정
서버 접속 후:
```bash
cd upbit-grid-bot
nano .env
```

다음 내용을 입력하세요:
```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
ADMIN_USER_ID=your_user_id_here

# Upbit API Keys (IP 화이트리스트 필수!)
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here
```

저장: `Ctrl+O` → Enter, 종료: `Ctrl+X`

### 3. 봇 시작
```bash
sudo systemctl start upbit-grid-bot
```

또는 로컬에서:
```powershell
.\manage_server.ps1 start
```

### 4. 상태 확인
```powershell
.\manage_server.ps1 status
.\manage_server.ps1 logs    # 실시간 로그 보기
```

## 🎮 Discord 명령어

| 명령어 | 설명 |
|--------|------|
| `!시작` | 그리드 트레이딩 설정 시작 (위자드 방식) |
| `!종료` | 트레이딩 중단 |
| `!상태` | 현재 상태 확인 (계약 수, 현재가, 손익) |
| `!리포트` | 최근 10건 거래 내역 |
| `!청산` | 모든 포지션 정리 (구현 예정) |

## 🛠️ 관리 스크립트 사용법

`manage_server.ps1` (Windows PowerShell)

```powershell
.\manage_server.ps1 connect    # 서버 접속
.\manage_server.ps1 status     # 봇 상태 확인
.\manage_server.ps1 start      # 봇 시작
.\manage_server.ps1 stop       # 봇 중지
.\manage_server.ps1 restart    # 봇 재시작
.\manage_server.ps1 logs       # 실시간 로그
.\manage_server.ps1 edit-env   # .env 수정
.\manage_server.ps1 update     # 코드 업데이트 후 재시작
```

## 📚 상세 문서

- **[DEPLOY.md](DEPLOY.md)**: 배포 및 관리 가이드
- **[DOCS/PRD.md](DOCS/PRD.md)**: 제품 요구사항 문서
- **[DOCS/Technical_Design.md](DOCS/Technical_Design.md)**: 기술 설계 문서

## ⚠️ 주의사항

1. **Upbit API IP 화이트리스트**: 서버의 공인 IP를 Upbit API 키 관리 페이지에서 반드시 등록하세요.
2. **Discord Admin ID**: `ADMIN_USER_ID`에 등록된 사용자만 봇 명령어를 사용할 수 있습니다.
3. **최소 자금**: 그리드 설정 시 필요한 자금이 부족하면 시작이 거부됩니다.
4. **테스트**: 처음에는 소액으로 테스트 후 본격 운영하세요.

## 🔧 문제 해결

### 봇이 실행되지 않을 때
```powershell
.\manage_server.ps1 logs
```
로그를 확인하여 오류 메시지를 찾으세요.

### API 오류가 발생할 때
- Upbit API IP 화이트리스트 확인
- `.env` 파일의 키 값이 정확한지 확인
- 봇 재시작: `.\manage_server.ps1 restart`

### Discord 명령어가 작동하지 않을 때
- `ADMIN_USER_ID`가 정확한지 확인
- Discord Developer Portal에서 Message Content Intent가 활성화되어 있는지 확인

## 📝 라이센스

MIT License

## 👨‍💻 개발자

gostop400401
