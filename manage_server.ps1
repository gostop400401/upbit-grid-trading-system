# Upbit Grid Trading Bot - 서버 관리 스크립트 (PowerShell)
# Usage: .\manage_server.ps1 [명령어]

param(
    [string]$Command = "help"
)

$SERVER_KEY = "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key"
$SERVER_IP = "168.138.214.180"
$SERVER_USER = "ubuntu"
$BOT_DIR = "upbit-grid-bot"

function Show-Help {
    Write-Host "🤖 Upbit Grid Bot 서버 관리 도구" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "사용법: .\manage_server.ps1 [명령어]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "명령어:"
    Write-Host "  connect     - 서버 접속"
    Write-Host "  status      - 봇 상태 확인"
    Write-Host "  start       - 봇 시작"
    Write-Host "  stop        - 봇 중지"
    Write-Host "  restart     - 봇 재시작"
    Write-Host "  logs        - 실시간 로그 보기"
    Write-Host "  edit-env    - .env 파일 수정"
    Write-Host "  update      - GitHub에서 최신 코드 받기"
}

switch ($Command) {
    "connect" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP"
    }
    "status" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl status upbit-grid-bot"
    }
    "start" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl start upbit-grid-bot"
        Write-Host "✅ 봇을 시작했습니다." -ForegroundColor Green
    }
    "stop" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl stop upbit-grid-bot"
        Write-Host "🛑 봇을 중지했습니다." -ForegroundColor Red
    }
    "restart" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl restart upbit-grid-bot"
        Write-Host "🔄 봇을 재시작했습니다." -ForegroundColor Yellow
    }
    "logs" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo journalctl -u upbit-grid-bot -f"
    }
    "edit-env" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "cd $BOT_DIR; nano .env"
    }
    "update" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "cd $BOT_DIR; git pull; sudo systemctl restart upbit-grid-bot"
        Write-Host "✅ 업데이트 및 재시작 완료!" -ForegroundColor Green
    }
    default {
        Show-Help
    }
}
