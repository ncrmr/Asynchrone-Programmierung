import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class DiscordBotHandler:

    def __init__(self, token: str, command_prefix: str = "!"):
        self.token = token
        self.command_prefix = command_prefix
        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=discord.Intents.default(),
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

    async def discord_bot_task(self):
        async with self.bot:
            await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()

