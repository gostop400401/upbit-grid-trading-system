import discord
from discord.ext import commands
import os
import logging
import asyncio
from typing import Optional
from modules.trading_manager import TradingManager
from models.contract import Contract
from database.database import get_config

logger = logging.getLogger("TradingSystem")

class TickerSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected_ticker = None

    @discord.ui.button(label="KRW-USDT", style=discord.ButtonStyle.primary)
    async def usdt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_ticker = "KRW-USDT"
        await interaction.response.send_message(f"✅ {self.selected_ticker} 선택됨.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="KRW-BTC", style=discord.ButtonStyle.secondary)
    async def btc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_ticker = "KRW-BTC"
        await interaction.response.send_message(f"✅ {self.selected_ticker} 선택됨.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="KRW-ETH", style=discord.ButtonStyle.secondary)
    async def eth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_ticker = "KRW-ETH"
        await interaction.response.send_message(f"✅ {self.selected_ticker} 선택됨.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="KRW-XRP", style=discord.ButtonStyle.secondary)
    async def xrp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_ticker = "KRW-XRP"
        await interaction.response.send_message(f"✅ {self.selected_ticker} 선택됨.", ephemeral=True)
        self.stop()
        
    @discord.ui.button(label="직접 입력", style=discord.ButtonStyle.gray)
    async def custom_button(self, interaction: discord.Interaction, button: discord.ui.Button):
         self.selected_ticker = "CUSTOM"
         await interaction.response.send_message("채팅창에 티커를 직접 입력해주세요 (예: KRW-SOL).", ephemeral=True)
         self.stop()

class TradingBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot, trading_manager: TradingManager):
        self.bot = bot
        self.trading_manager = trading_manager
        self.admin_id = int(os.getenv("ADMIN_USER_ID", "0"))

    async def is_admin(self, ctx):
        logger.info(f"Checking Admin: User {ctx.author.id} vs Admin {self.admin_id}")
        if ctx.author.id != self.admin_id:
            logger.warning("Admin check failed.")
            await ctx.send(f"🚫 관리자만 사용할 수 있는 명령어입니다. (Your ID: {ctx.author.id})")
            return False
        return True

    @commands.command(name="시작")
    async def cmd_start(self, ctx):
        if not await self.is_admin(ctx): return

        if self.trading_manager.is_running:
            await ctx.send("이미 트레이딩이 진행 중입니다.")
            return

        # Simple Wizard
        view = TickerSelectView()
        await ctx.send("트레이딩 설정을 시작합니다.\n**주의: 현재가와 같거나 낮은 그리드 라인은 즉시 매수 체결될 수 있습니다.**\n거래할 코인을 선택해주세요:", view=view)
        
        # Wait for button click
        await view.wait()
        
        if view.selected_ticker is None:
            await ctx.send("시간 초과 또는 선택 취소됨.")
            return

        ticker = view.selected_ticker
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # If custom input needed
            if ticker == "CUSTOM":
                await ctx.send("티커를 입력해주세요 (예: KRW-DOGE):")
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                ticker = msg.content.strip()
            
            await ctx.send(f"'{ticker}' 선택됨. 최소 가격(Min Price)을 입력해주세요:")
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            min_price = float(msg.content.strip())
            
            await ctx.send(f"최대 가격(Max Price)을 입력해주세요:")
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            max_price = float(msg.content.strip())
            
            await ctx.send(f"그리드 간격(Grid Interval, 단위: 원/USDT)을 입력해주세요 (예: 2.0):")
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            grid_interval = float(msg.content.strip())
            
            # Calculate Expected Grid Count
            if grid_interval <= 0:
                await ctx.send("간격은 0보다 커야 합니다. 다시 시작해주세요.")
                return
                
            grid_count = int((max_price - min_price) / grid_interval) + 1
            
            await ctx.send(f"그리드 당 주문 수량(단위: 코인 개수, 예: 4 USDT, 0.001 BTC)을 입력해주세요:")
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            amount_per_grid = float(msg.content.strip())
            
            profit_interval = 3.0 # Fixed default to 3 KRW as requested
            
            # Validate Balance
            validation = await self.trading_manager.validate_balance(
                ticker, grid_count, amount_per_grid, min_price, max_price
            )
            
            await ctx.send(validation['message'])
            
            if not validation['valid']:
                await ctx.send("⚠️ 자금이 부족하여 시작할 수 없습니다. 설정을 변경하거나 자금을 충전해주세요.")
                return

            config = {
                'coin_ticker': ticker,
                'min_price': min_price,
                'max_price': max_price,
                'grid_interval': grid_interval,
                'grid_count': grid_count,
                'amount_per_grid': amount_per_grid,
                'profit_interval': profit_interval
            }
            
            confirm_msg = f"설정 확인:\n" \
                          f"- 코인: {ticker}\n" \
                          f"- 범위: {min_price} ~ {max_price}\n" \
                          f"- 간격: {grid_interval}\n" \
                          f"- 에상 그리드 수: {grid_count}개\n" \
                          f"- 주문 수량: {amount_per_grid}\n" \
                          f"- 익절 폭: {profit_interval}\n\n" \
                          f"'시작'을 입력하면 매매를 시작합니다."
            
            await ctx.send(confirm_msg)
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.strip() == "시작":
                msg_res = await self.trading_manager.start_trading(config)
                await ctx.send(f"✅ {msg_res}")
            else:
                await ctx.send("시작 취소됨.")
                
        except asyncio.TimeoutError:
            await ctx.send("시간 초과로 설정이 취소되었습니다.")
        except ValueError:
            await ctx.send("잘못된 입력 형식입니다. 숫자를 입력해주세요.")
        except Exception as e:
            logger.error(f"Wizard Error: {e}")
            await ctx.send(f"설정 중 오류가 발생했습니다: {e}")

    @commands.command(name="종료")
    async def cmd_stop(self, ctx):
        if not await self.is_admin(ctx): return
        
        await self.trading_manager.stop_trading()
        await ctx.send("🛑 트레이딩이 중단되었습니다.")

    @commands.command(name="상태")
    async def cmd_status(self, ctx):
        if not await self.is_admin(ctx): return
        
        if not self.trading_manager.is_running:
            await ctx.send("비활성 상태입니다.")
            return
            
        active_contracts = await Contract.get_active_contracts()
        current_price = self.trading_manager.handler.current_price
        
        embed = discord.Embed(title="Trading Status", color=0x00ff00)
        embed.add_field(name="Active Contracts", value=f"{len(active_contracts)} 개", inline=True)
        embed.add_field(name="Current Price", value=f"{current_price}", inline=True)
        
        # Calculate Unrealiased PnL?
        total_buy_val = sum(c.buy_price * c.buy_amount for c in active_contracts)
        current_val = sum(current_price * c.buy_amount for c in active_contracts) if current_price and current_price > 0 else 0
        unrealized_pnl = current_val - total_buy_val
        
        embed.add_field(name="Unrealized PnL", value=f"{unrealized_pnl:.2f}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="리포트")
    async def cmd_report(self, ctx):
        if not await self.is_admin(ctx): return
        
        # Fetch closed contracts (limit 10 for now)
        from database.database import execute_read
        rows = await execute_read("SELECT * FROM contracts WHERE status='CLOSED' ORDER BY finished_at DESC LIMIT 10", fetch_all=True)
        
        if not rows:
            await ctx.send("마감된 계약 내역이 없습니다.")
            return
            
        msg = "**최근 10건 거래 리포트**\n```\n"
        msg += f"{'ID':<4} | {'Buy':<8} | {'Sell':<8} | {'Profit':<8}\n"
        msg += "-"*35 + "\n"
        for row in rows:
            p = row['profit'] if row['profit'] else 0.0
            msg += f"{row['id']:<4} | {row['buy_price']:<8} | {row['sell_price']:<8} | {p:<8.2f}\n"
        msg += "```"
        await ctx.send(msg)

    @commands.command(name="청산")
    async def cmd_liquidate(self, ctx):
         if not await self.is_admin(ctx): return
         await ctx.send("⚠️ 청산 기능은 아직 구현되지 않았습니다.")


class DiscordBot(commands.Bot):
    def __init__(self, trading_manager: TradingManager):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.trading_manager = trading_manager
        self.target_channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
        
        # Link notification callback
        self.trading_manager.set_notification_callback(self.send_notification)

    async def send_notification(self, message: str):
        channel = self.get_channel(self.target_channel_id)
        if channel:
            await channel.send(message)
        else:
            logger.warning("Target channel not found for notification.")

    async def setup_hook(self):
        # Load Cogs
        await self.add_cog(TradingBotCog(self, self.trading_manager))
        logger.info("TradingBotCog loaded.")
        
        # Load Slash Commands Cog
        try:
            from modules.slash_commands import SlashCommandsCog
            await self.add_cog(SlashCommandsCog(self, self.trading_manager))
            logger.info("SlashCommandsCog loaded.")
            
            # Sync slash commands with Discord
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        channel = self.get_channel(self.target_channel_id)
        if channel:
            await channel.send("🚀 업비트 그리드 트레이딩 봇이 시작되었습니다.")
        else:
            logger.warning(f"Target channel {self.target_channel_id} not found.")

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # Debug log for message reception
        # logger.info(f"Received message: '{message.content}'")
        
        await self.process_commands(message)
