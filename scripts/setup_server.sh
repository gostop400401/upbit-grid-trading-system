#!/bin/bash

# Upbit Grid Trading Bot - 서버 자동 설정 스크립트
# Usage: ./scripts/setup_server.sh

echo "🚀 업비트 그리드 트레이딩 봇 서버 설정을 시작합니다..."

# 1. 시스템 패키지 업데이트 및 필수 프로그램 설치
echo "📦 필수 패키지 설치 중..."
sudo apt update
sudo apt install -y python3-pip python3-venv

# 2. 가상환경 설정
echo "🐍 Python 가상환경(venv) 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "ℹ️ 가상환경이 이미 존재합니다."
fi

# 3. 의존성 설치
echo "📚 라이브러리 설치 중..."
./venv/bin/pip install -r requirements.txt

# 4. .env 파일 설정
if [ ! -f ".env" ]; then
    echo "⚙️ .env 파일 생성 중..."
    cat > .env << 'EOF'
# Discord Bot Configuration
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID=YOUR_CHANNEL_ID
ADMIN_USER_ID=YOUR_ADMIN_USER_ID

# Upbit API Keys
UPBIT_ACCESS_KEY=YOUR_UPBIT_ACCESS_KEY
UPBIT_SECRET_KEY=YOUR_UPBIT_SECRET_KEY
EOF
    echo "⚠️ .env 파일이 생성되었습니다. API 키를 입력해주세요!"
else
    echo "ℹ️ .env 파일이 이미 존재합니다."
fi

# 5. 로그 디렉토리 생성
mkdir -p logs

# 6. Systemd 서비스 등록
echo "🤖 Systemd 서비스 등록 중..."
CURRENT_DIR=$(pwd)
SERVICE_FILE_CONTENT="[Unit]
Description=Upbit Grid Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
EnvironmentFile=$CURRENT_DIR/.env

[Install]
WantedBy=multi-user.target"

echo "$SERVICE_FILE_CONTENT" | sudo tee /etc/systemd/system/upbit-grid-bot.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable upbit-grid-bot

echo "🎉 설정이 완료되었습니다!"
echo "----------------------------------------"
echo "1. 'nano .env' 명령어로 API 키를 입력하세요."
echo "2. 'sudo systemctl start upbit-grid-bot' 으로 봇을 실행하세요."
echo "3. Discord에서 작동을 확인하세요."
echo "----------------------------------------"
