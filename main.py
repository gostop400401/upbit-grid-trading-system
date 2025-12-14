import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure modules in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils import setup_logger
from database.database import init_db
from modules.upbit_handler import UpbitHandler
from modules.trading_manager import TradingManager
from modules.discord_bot import DiscordBot

logger = setup_logger()

async def main():
    logger.info("Starting Upbit Grid Trading System...")
    
    # 1. Load Env
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")
    
    if not discord_token or not access_key or not secret_key:
        logger.error("Missing configuration in .env. Please check DISCORD_TOKEN/UPBIT_KEYS.")
        return

    # 2. Init DB
    await init_db()
    
    # 3. Initialize Components
    handler = UpbitHandler(access_key, secret_key)
    manager = TradingManager(handler)
    bot = DiscordBot(manager)

    # 4. State Recovery & Startup Check
    # We should run recovery once before accepting commands
    try:
        await manager.recover_state()
    except Exception as e:
        logger.error(f"State Recovery Failed: {e}")
        # Continue? Or stop? Continue, manual check might be needed.

    # 5. Start Discord Bot & Trading Loop
    # We need to run the bot. `bot.start` is a coroutine.
    # We also need to run the Upbit WebSocket if monitoring requires it.
    # TradingManager will start monitoring task when `start_trading` is called.
    # But if we recovered enabled/running state, we might need to Auto-Start trading?
    # Current logic: `recover_state` only checks orders. `start_trading` sets `is_running=True`.
    # If the bot crashed, we want it to Resume Trading if it was running.
    # We can check DB 'config' or similar? 
    # Let's assume user must type '!시작' to RE-ENABLE the loop logic for safety in V1,
    # OR better: Check 'last_grid_config' in DB. If exists, ask user to resume?
    # For now, let's keep it manual start via Discord for safety.
    
    # Start Bot
    async with bot:
        await bot.start(discord_token)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System Shutdown by User.")
    except Exception as e:
        logger.error(f"System Crash: {e}", exc_info=True)
