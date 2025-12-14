#!/bin/bash
# 서버 배포 자동화 스크립트

SERVER_KEY="C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key"
SERVER_IP="168.138.214.180"
SERVER_USER="ubuntu"

echo "🚀 서버에 업비트 그리드 봇 배포를 시작합니다..."

# 1. Git Clone (이미 완료)
echo "✅ Git Clone 완료"

# 2. Setup Script 실행
echo "📦 서버 설정 중..."
ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd upbit-grid-bot
chmod +x scripts/setup_server.sh
./scripts/setup_server.sh
ENDSSH

echo "🎉 배포 완료!"
echo "이제 .env 파일을 설정하고 봇을 시작하세요:"
echo "  ssh -i \"$SERVER_KEY\" $SERVER_USER@$SERVER_IP"
echo "  cd upbit-grid-bot"
echo "  nano .env"
echo "  sudo systemctl start upbit-grid-bot"
