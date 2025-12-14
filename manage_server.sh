#!/bin/bash

# Upbit Grid Trading Bot - 서버 관리 스크립트
# Usage: ./manage_server.sh [명령어]

SERVER_KEY="C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key"
SERVER_IP="168.138.214.180"
SERVER_USER="ubuntu"
BOT_DIR="upbit-grid-bot"

function show_help() {
    echo "🤖 Upbit Grid Bot 서버 관리 도구"
    echo ""
    echo "사용법: ./manage_server.sh [명령어]"
    echo ""
    echo "명령어:"
    echo "  connect     - 서버 접속"
    echo "  status      - 봇 상태 확인"
    echo "  start       - 봇 시작"
    echo "  stop        - 봇 중지"
    echo "  restart     - 봇 재시작"
    echo "  logs        - 실시간 로그 보기"
    echo "  edit-env    - .env 파일 수정"
    echo "  update      - GitHub에서 최신 코드 받기"
}

case "$1" in
    connect)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP
        ;;
    status)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP 'sudo systemctl status upbit-grid-bot'
        ;;
    start)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP 'sudo systemctl start upbit-grid-bot'
        echo "✅ 봇을 시작했습니다."
        ;;
    stop)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP 'sudo systemctl stop upbit-grid-bot'
        echo "🛑 봇을 중지했습니다."
        ;;
    restart)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP 'sudo systemctl restart upbit-grid-bot'
        echo "🔄 봇을 재시작했습니다."
        ;;
    logs)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP 'sudo journalctl -u upbit-grid-bot -f'
        ;;
    edit-env)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP "cd $BOT_DIR; nano .env"
        ;;
    update)
        ssh -i "$SERVER_KEY" $SERVER_USER@$SERVER_IP "cd $BOT_DIR; git pull; sudo systemctl restart upbit-grid-bot"
        echo "✅ 업데이트 및 재시작 완료!"
        ;;
    *)
        show_help
        ;;
esac
