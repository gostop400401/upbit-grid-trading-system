"""
Discord Slash Commands for Upbit Grid Trading Bot
Provides user-friendly slash commands with buttons and interactive UI
"""
import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
from typing import Optional
from datetime import datetime

from modules.trading_manager import TradingManager
from models.contract import Contract
from models.trade import Trade

logger = logging.getLogger("TradingSystem")


class StatusView(discord.ui.View):
    """Interactive buttons for status command"""
    def __init__(self, trading_manager: TradingManager):
        super().__init__(timeout=300)  # 5분 타임아웃
        self.trading_manager = trading_manager
    
    @discord.ui.button(label="📋 상세 포지션", style=discord.ButtonStyle.primary)
    async def positions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # /포지션 명령어 실행과 동일한 동작
        embed = await create_positions_embed(self.trading_manager)
        view = RefreshView(self.trading_manager, "positions")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="💰 수익 상세", style=discord.ButtonStyle.success)
    async def profit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # /수익 명령어 실행과 동일한 동작
        embed = await create_profit_embed(self.trading_manager)
        view = RefreshView(self.trading_manager, "profit")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="🔄 새로고침", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # 현재 명령어 재실행
        embed = await create_status_embed(self.trading_manager)
        view = StatusView(self.trading_manager)
        await interaction.edit_original_response(embed=embed, view=view)


class RefreshView(discord.ui.View):
    """Simple refresh button for detail views"""
    def __init__(self, trading_manager: TradingManager, view_type: str):
        super().__init__(timeout=300)
        self.trading_manager = trading_manager
        self.view_type = view_type
    
    @discord.ui.button(label="🔄 새로고침", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if self.view_type == "positions":
            embed = await create_positions_embed(self.trading_manager)
        elif self.view_type == "profit":
            embed = await create_profit_embed(self.trading_manager)
        else:
            embed = await create_status_embed(self.trading_manager)
        
        view = RefreshView(self.trading_manager, self.view_type)
        await interaction.edit_original_response(embed=embed, view=view)


async def create_status_embed(trading_manager: TradingManager) -> discord.Embed:
    """Create status embed"""
    embed = discord.Embed(
        title="📊 Upbit Grid Trading 시스템 상태",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # 실행 상태
    is_running = trading_manager.is_running
    status_emoji = "✅" if is_running else "⏸️"
    status_text = "실행 중" if is_running else "정지됨"
    
    embed.add_field(
        name="🔹 실행 상태",
        value=f"{status_emoji} {status_text}",
        inline=True
    )
    
    # 코인 및 현재가
    if trading_manager.config:
        ticker = trading_manager.config.get('coin_ticker', 'N/A')
        try:
            current_price = await trading_manager.handler.get_current_price(ticker)
            price_text = f"{current_price:,.0f}원" if current_price else "조회 실패"
        except:
            price_text = "조회 실패"
        
        embed.add_field(
            name="🔹 코인",
            value=ticker,
            inline=True
        )
        embed.add_field(
            name="🔹 현재가",
            value=price_text,
            inline=True
        )
    
    # 포지션 현황
    active_contracts = await Contract.get_active_contracts()
    pending_count = len(trading_manager.pending_buy_orders)
    pending_prices = sorted(set(trading_manager.pending_buy_orders.values())) if pending_count > 0 else []
    
    position_info = f"├─ 활성 계약: {len(active_contracts)}개\n"
    position_info += f"├─ 미체결 매수: {pending_count}개"
    if pending_prices:
        prices_str = ", ".join([f"{p:.0f}" for p in pending_prices[:5]])
        if len(pending_prices) > 5:
            prices_str += "..."
        position_info += f" ({prices_str}원)"
    
    if active_contracts:
        avg_price = sum(float(c.buy_price) for c in active_contracts) / len(active_contracts)
        position_info += f"\n└─ 평균 진입가: {avg_price:,.0f}원"
    
    embed.add_field(
        name="📈 포지션 현황",
        value=position_info,
        inline=False
    )
    
    # 수익 현황 (실현 손익만)
    try:
        from database.database import execute_read
        profit_data = await execute_read(
            "SELECT SUM(profit) as total_profit, COUNT(*) as trade_count FROM trades WHERE type = 'SELL'"
        )
        
        if profit_data and profit_data.get('total_profit'):
            total_profit = float(profit_data['total_profit'])
            trade_count = profit_data['trade_count']
            
            # 오늘 거래
            today_data = await execute_read(
                "SELECT COUNT(*) as today_count FROM trades WHERE type = 'SELL' AND DATE(executed_at) = DATE('now', 'localtime')"
            )
            today_count = today_data['today_count'] if today_data else 0
            
            profit_emoji = "📈" if total_profit > 0 else "📉" if total_profit < 0 else "➖"
            profit_info = f"├─ 총 실현 손익: {profit_emoji} {total_profit:+,.0f}원\n"
            profit_info += f"├─ 총 거래 횟수: {trade_count}회\n"
            profit_info += f"└─ 오늘 거래: {today_count}회"
        else:
            profit_info = "아직 거래 내역이 없습니다"
        
        embed.add_field(
            name="💰 수익 현황",
            value=profit_info,
            inline=False
        )
    except Exception as e:
        logger.error(f"Error fetching profit data: {e}")
    
    # 가동 시간
    if hasattr(trading_manager, 'bot_start_time'):
        uptime = datetime.now().timestamp() - trading_manager.bot_start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        embed.add_field(
            name="⏱️ 가동 시간",
            value=f"{hours}시간 {minutes}분",
            inline=False
        )
    
    embed.set_footer(text="버튼을 클릭하여 상세 정보를 확인하세요")
    
    return embed


async def create_positions_embed(trading_manager: TradingManager) -> discord.Embed:
    """Create positions detail embed"""
    active_contracts = await Contract.get_active_contracts()
    
    if not active_contracts:
        embed = discord.Embed(
            title="📋 활성 계약 목록",
            description="✅ 현재 활성 계약이 없습니다\n모든 포지션이 청산되었습니다.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        return embed
    
    embed = discord.Embed(
        title=f"📋 활성 계약 목록 (총 {len(active_contracts)}개)",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # 최대 10개까지만 표시
    for i, contract in enumerate(active_contracts[:10]):
        profit_interval = contract.target_price - contract.buy_price
        
        # 현재 미실현 손익 계산 (간단 버전)
        try:
            current_price = await trading_manager.handler.get_current_price(contract.coin_ticker)
            if current_price:
                unrealized_profit = (current_price - contract.buy_price) * contract.buy_amount
                unrealized_rate = (current_price - contract.buy_price) / contract.buy_price * 100
                unrealized_text = f"{unrealized_profit:+,.0f}원 ({unrealized_rate:+.2f}%)"
            else:
                unrealized_text = "계산 불가"
        except:
            unrealized_text = "계산 불가"
        
        contract_info = f"├─ 진입가: {contract.buy_price:,.0f}원\n"
        contract_info += f"├─ 목표가: {contract.target_price:,.0f}원 (+{profit_interval:.0f}원)\n"
        contract_info += f"├─ 수량: {contract.buy_amount} {contract.coin_ticker.split('-')[1]}\n"
        contract_info += f"├─ 미실현 손익: {unrealized_text}\n"
        contract_info += f"└─ 체결 시간: {contract.created_at[:16] if contract.created_at else 'N/A'}"
        
        embed.add_field(
            name=f"Contract #{contract.id}",
            value=contract_info,
            inline=False
        )
    
    if len(active_contracts) > 10:
        embed.add_field(
            name="ℹ️ 안내",
            value=f"+ {len(active_contracts) - 10}개 더 있습니다",
            inline=False
        )
    
    return embed


async def create_profit_embed(trading_manager: TradingManager) -> discord.Embed:
    """Create profit statistics embed"""
    embed = discord.Embed(
        title="💰 거래 통계",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    try:
        from database.database import execute_read
        
        # 전체 통계
        all_stats = await execute_read(
            "SELECT SUM(profit) as total_profit, COUNT(*) as trade_count, AVG(profit) as avg_profit FROM trades WHERE type = 'SELL'"
        )
        
        if all_stats and all_stats.get('trade_count', 0) > 0:
            total_profit = float(all_stats['total_profit'] or 0)
            trade_count = all_stats['trade_count']
            avg_profit = float(all_stats['avg_profit'] or 0)
            
            # 승률 (그리드 트레이딩은 보통 100%)
            win_rate = 100  # 그리드 트레이딩 특성상 익절로만 청산
            
            all_info = f"├─ 총 실현 손익: {total_profit:+,.0f}원\n"
            all_info += f"├─ 총 거래 횟수: {trade_count}회\n"
            all_info += f"├─ 평균 거래당 수익: {avg_profit:+,.0f}원\n"
            all_info += f"└─ 승률: {win_rate}%"
            
            embed.add_field(
                name="📊 전체 통계",
                value=all_info,
                inline=False
            )
            
            # 최고 거래
            best_trade = await execute_read(
                "SELECT profit, executed_at FROM trades WHERE type = 'SELL' ORDER BY profit DESC LIMIT 1"
            )
            
            if best_trade:
                best_profit = float(best_trade['profit'])
                best_time = best_trade['executed_at'][:16] if best_trade['executed_at'] else 'N/A'
                
                best_info = f"├─ 수익금: +{best_profit:,.0f}원\n"
                best_info += f"└─ 일시: {best_time}"
                
                embed.add_field(
                    name="🏆 최고 거래",
                    value=best_info,
                    inline=False
                )
            
            # 오늘 거래
            today_stats = await execute_read(
                "SELECT SUM(profit) as today_profit, COUNT(*) as today_count FROM trades WHERE type = 'SELL' AND DATE(executed_at) = DATE('now', 'localtime')"
            )
            
            if today_stats and today_stats.get('today_count', 0) > 0:
                today_profit = float(today_stats['today_profit'] or 0)
                today_count = today_stats['today_count']
                today_avg = today_profit / today_count if today_count > 0 else 0
                
                today_info = f"├─ 거래 횟수: {today_count}회\n"
                today_info += f"├─ 실현 손익: {today_profit:+,.0f}원\n"
                today_info += f"└─ 평균 수익: {today_avg:+,.0f}원"
                
                embed.add_field(
                    name="📈 오늘 거래",
                    value=today_info,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📈 오늘 거래",
                    value="오늘은 아직 거래가 없습니다",
                    inline=False
                )
        else:
            embed.description = "아직 거래 내역이 없습니다"
    
    except Exception as e:
        logger.error(f"Error creating profit embed: {e}")
        embed.description = f"통계 조회 중 오류 발생: {e}"
    
    return embed


class SlashCommandsCog(commands.Cog):
    """Modern slash commands for better UX"""
    
    def __init__(self, bot: commands.Bot, trading_manager: TradingManager):
        self.bot = bot
        self.trading_manager = trading_manager
        self.admin_id = int(os.getenv("ADMIN_USER_ID", "0"))
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user is admin"""
        return interaction.user.id == self.admin_id
    
    @app_commands.command(name="상태", description="시스템 현황 조회")
    async def status(self, interaction: discord.Interaction):
        """System status with interactive buttons"""
        if not self.is_admin(interaction):
            await interaction.response.send_message("🚫 관리자만 사용할 수 있습니다", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = await create_status_embed(self.trading_manager)
        view = StatusView(self.trading_manager)
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="포지션", description="활성 계약 상세 조회")
    async def positions(self, interaction: discord.Interaction):
        """Detailed positions view"""
        if not self.is_admin(interaction):
            await interaction.response.send_message("🚫 관리자만 사용할 수 있습니다", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = await create_positions_embed(self.trading_manager)
        view = RefreshView(self.trading_manager, "positions")
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="수익", description="거래 통계 조회")
    async def profit(self, interaction: discord.Interaction):
        """Profit statistics"""
        if not self.is_admin(interaction):
            await interaction.response.send_message("🚫 관리자만 사용할 수 있습니다", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = await create_profit_embed(self.trading_manager)
        view = RefreshView(self.trading_manager, "profit")
        
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog"""
    # Get trading_manager from bot
    trading_manager = getattr(bot, 'trading_manager', None)
    if trading_manager:
        await bot.add_cog(SlashCommandsCog(bot, trading_manager))
        logger.info("SlashCommandsCog loaded successfully")
    else:
        logger.error("trading_manager not found in bot")
