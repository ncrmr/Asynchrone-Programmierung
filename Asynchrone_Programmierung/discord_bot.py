import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class DiscordBotHandler:

    def __init__(self, token: str, channel: int, command_prefix: str = "!", modbus_client=None):
        self.token = token
        self.channel_id = channel
        self.command_prefix = command_prefix
        self.modbus_client = modbus_client
        self.channel = None

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

        @self.bot.command(name="led_on")
        async def cmd_led_on(ctx):
            if self.modbus_client:
                result = await self.modbus_client.write_output(0, True)
                if result:
                    await ctx.send("LED eingeschaltet!")
                else:
                    await ctx.send("Fehler beim Einschalten der LED.")
            else:
                await ctx.send("Modbus client nicht verfügbar.")

        @self.bot.command(name="led_off")
        async def cmd_led_off(ctx):
            if self.modbus_client:
                result = await self.modbus_client.write_output(0, False)
                if result:
                    await ctx.send("LED ausgeschaltet!")
                else:
                    await ctx.send("Fehler beim Ausschalten der LED.")
            else:
                await ctx.send("Modbus client nicht verfügbar.")

    async def on_ready(self):
        logger.info("Der Bot ist jetzt online")
        self.channel = self.bot.get_channel(self.channel_id)
        if self.channel:
            await self.channel.send("🟢 Ich bin jetzt online!")
            await self.channel.send("Hier eine Liste der gültigen Befehle:" \
            f"\n{self.command_prefix}ping - Testet die Verbindung zum Bot" \
            f"\n{self.command_prefix}led_on - Schaltet die LED ein" \
            f"\n{self.command_prefix}led_off - Schaltet die LED aus"
            )
        else:
            logger.warning(f"Kanal {self.channel_id} nicht gefunden")

    async def notify_input_change(self, input_bit: int, state: bool):
        channel = self.channel or self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(f"Digitaler Eingang {input_bit} hat sich geändert: {'AN' if state else 'AUS'}")
        else:
            logger.warning("Kein Kanal verfügbar für Input-Change-Benachrichtigung")

    async def discord_bot_task(self):
        async with self.bot:
            await self.bot.start(self.token)

    async def stop(self):
        logger.info("Der Bot ist jetzt offline")
        await self.bot.close()
