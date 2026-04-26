import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class DiscordBotHandler:

    def __init__(self, token: str, channel: int, command_prefix: str = "!"):
        self.token = token
        self.channel_id = channel
        self.command_prefix = command_prefix

        intents = discord.Intents.default()
        intents.message_content = True  # wichtig für Commands!

        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents,
        )

        # Register event handlers
        self.bot.event(self.on_ready)

        # Register commands
        self._register_commands()

    def _register_commands(self):
        @self.bot.command(name="ping")
        async def cmd_ping(ctx):
            await ctx.send(f"🏓 Pong!")

    async def on_ready(self):
        print("Ich bin jetzt online")
        channel = self.bot.get_channel(self.channel_id)
        await channel.send("🟢 Ich bin jetzt online!")

    async def discord_bot_task(self):
        async with self.bot:
            await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()
