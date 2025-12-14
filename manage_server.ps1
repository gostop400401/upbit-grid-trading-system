# Upbit Grid Trading Bot - Server Management Script (PowerShell)
# Usage: .\manage_server.ps1 [Command]

param(
    [string]$Command = "help"
)

$SERVER_KEY = "C:\Users\MINIMON\Desktop\AI작업\5.bn funding fee\ssh-key-2025-03-01.key"
$SERVER_IP = "168.138.214.180"
$SERVER_USER = "ubuntu"
$BOT_DIR = "upbit-grid-bot"

function Show-Help {
    Write-Host "Upbit Grid Bot Server Management Tool" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\manage_server.ps1 [Command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  connect     - Connect to server"
    Write-Host "  status      - Check bot status"
    Write-Host "  start       - Start bot"
    Write-Host "  stop        - Stop bot"
    Write-Host "  restart     - Restart bot"
    Write-Host "  logs        - View real-time logs"
    Write-Host "  edit-env    - Edit .env file"
    Write-Host "  update      - Pull latest code from GitHub and restart"
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
        Write-Host "Bot started successfully." -ForegroundColor Green
    }
    "stop" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl stop upbit-grid-bot"
        Write-Host "Bot stopped." -ForegroundColor Red
    }
    "restart" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo systemctl restart upbit-grid-bot"
        Write-Host "Bot restarted." -ForegroundColor Yellow
    }
    "logs" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "sudo journalctl -u upbit-grid-bot -f"
    }
    "edit-env" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "cd $BOT_DIR; nano .env"
    }
    "update" {
        ssh -i $SERVER_KEY "$SERVER_USER@$SERVER_IP" "cd $BOT_DIR; git pull; sudo systemctl restart upbit-grid-bot"
        Write-Host "Update and restart complete!" -ForegroundColor Green
    }
    default {
        Show-Help
    }
}
