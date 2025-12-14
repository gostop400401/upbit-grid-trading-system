# Upbit Grid Trading Bot - 관리 매뉴얼

이 문서는 클라우드 서버에 설치된 업비트 그리드 트레이딩 봇을 **관리하고 유지보수하는 방법**을 설명합니다.

---

## 1. 서버 접속 (SSH)

모든 작업은 서버에 접속해서 수행합니다.

**접속 명령어** (터미널에 복사/붙여넣기):
```powershell
ssh -i "경로/키파일.key" ubuntu@서버IP주소
```
*(접속 후 `ubuntu@...` 같은 프롬프트가 나오면 성공입니다)*

---

## 2. 봇 끄고 켜기 (서비스 관리)

이 봇은 리눅스의 **`systemd`** 시스템에 의해 24시간 자동 실행되고 있습니다.

### 🟢 봇 상태 확인
봇이 잘 돌고 있는지 궁금할 때:
```bash
sudo systemctl status upbit-grid-bot
```
*   `Active: active (running)` 초록색 글자가 보이면 정상입니다.

### 🔄 봇 재시작
설정을 바꾸거나 코드를 업데이트했을 때:
```bash
sudo systemctl restart upbit-grid-bot
```

### 🔴 봇 중지
잠시 봇을 꺼두고 싶을 때:
```bash
sudo systemctl stop upbit-grid-bot
```

### ⚪ 봇 시작
꺼져있는 봇을 다시 켤 때:
```bash
sudo systemctl start upbit-grid-bot
```

---

## 3. 로그 확인 (실시간 감시)

봇이 무슨 일을 하고 있는지, 에러는 없는지 실시간으로 봅니다.

### 📜 실시간 로그 보기
```bash
sudo journalctl -u upbit-grid-bot -f
```
*   나갈 때는 `Ctrl` + `C`를 누르세요.

### 📋 지난 로그 보기 (최근 50줄)
```bash
sudo journalctl -u upbit-grid-bot -n 50 --no-pager
```

---

## 4. 설정 변경 (API 키 등)

API 키가 바뀌거나 디스코드 채널을 바꿀 때 `.env` 파일을 수정합니다.

1.  **설정 파일 열기**:
    ```bash
    nano ~/upbit-grid-bot/.env
    ```
2.  **수정**: 방향키로 이동해서 값을 변경합니다.
3.  **저장**: `Ctrl` + `O` -> `Enter`
4.  **종료**: `Ctrl` + `X`
5.  **적용**: 반드시 봇을 재시작해야 적용됩니다.
    ```bash
    sudo systemctl restart upbit-grid-bot
    ```

---

## 5. 최신 업데이트 (Git)

개발자가 코드를 수정해서 GitHub에 올렸다면, 서버에도 반영해야 합니다.

```bash
cd ~/upbit-grid-bot
git pull
sudo systemctl restart upbit-grid-bot
```

> **💡 꿀팁: 비공개(Private) 저장소 업데이트**
> 저장소를 **비공개**로 설정했다면 `git pull` 할 때 로그인을 물어봅니다.
> 복잡한 로그인 설정 대신, **업데이트할 때만 잠시 '공개(Public)'로 풀고** 업데이트 후 다시 비공개로 잠그는 방법이 가장 편합니다!

---

## 6. Discord 명령어 (봇 조작)

Discord에서 봇을 조작할 수 있습니다. (ADMIN_USER_ID로 설정된 사용자만 가능)

### 📋 주요 명령어
*   `!시작`: 그리드 트레이딩 설정 시작 (위자드 방식)
*   `!종료`: 트레이딩 중단
*   `!상태`: 현재 상태 확인 (활성 계약 수, 현재가, 미실현 손익 등)
*   `!리포트`: 최근 10건 거래 리포트
*   `!청산`: 모든 포지션 정리 (구현 예정)

---

## (참고) 초기 설치 방법
*이미 설치가 완료되었으므로 다시 할 필요는 없습니다. 참고용입니다.*

1.  코드 다운로드:
    ```bash
    git clone https://github.com/gostop400401/upbit-grid-trading-system.git upbit-grid-bot
    cd upbit-grid-bot
    ```

2.  설치 스크립트 실행:
    ```bash
    chmod +x scripts/setup_server.sh
    ./scripts/setup_server.sh
    ```

3.  설정 파일 생성:
    ```bash
    nano .env
    # API 키 입력 후 저장
    ```

4.  서비스 시작:
    ```bash
    sudo systemctl start upbit-grid-bot
    ```

5.  Discord에서 `!시작` 명령어로 테스트
