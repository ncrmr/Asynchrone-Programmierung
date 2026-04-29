import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class DiscordBotHandler:

    def __init__(self, token: str, channel: int, command_prefix: str = "!", modbus_client=None):
        # Discord-Token, Kanal-ID und Command-Präfix speichern.
        self.token = token
        self.channel_id = channel
        self.command_prefix = command_prefix
        # Modbus-Client, damit der Bot auf die Hardware zugreifen kann (z. B. um die LED zu schalten).
        self.modbus_client = modbus_client
        self.channel = None

        # Zustand der LED, damit der Bot den aktuellen Status kennt.
        self.led_state = False
        # Vorheriger Eingangszustand, wichtig zum Erkennen von Flanken.
        self.previous_input_state = None

        # Discord-Intents definieren: hier brauchen wir Nachrichteninhalt.
        # Intents sind eine Art Berechtigung, die der Bot benötigt, um bestimmte Informationen von Discord zu erhalten.
        intents = discord.Intents.default()
        intents.message_content = True  # wichtig für Commands!

        # Bot-Instanz erstellen, die die Befehle und Events verwaltet.
        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents,
        )

        # Event-Handler registrieren.
        self.bot.event(self.on_ready)

        # Befehle registrieren, die der Bot im Chat versteht.
        self._register_commands()

    def _register_commands(self):
        # Einfache Chat-Befehle. Diese sind asynchron, weil Discord async API nutzt.
        @self.bot.command(name="ping")
        async def cmd_ping(ctx):
            await ctx.send(f"🏓 Pong!")

        @self.bot.command(name="led_on")
        async def cmd_led_on(ctx):
            if self.modbus_client:
                result = await self.modbus_client.write_output(0, True)
                self.led_state = True
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
                self.led_state = False
                if result:
                    await ctx.send("LED ausgeschaltet!")
                else:
                    await ctx.send("Fehler beim Ausschalten der LED.")
            else:
                await ctx.send("Modbus client nicht verfügbar.")

        @self.bot.command(name="coil_on")
        async def cmd_coil_on(ctx):
            if self.modbus_client:
                result = await self.modbus_client.write_output(1, True)
                if result:
                    await ctx.send("Schütz eingeschaltet!")
                else:
                    await ctx.send("Fehler beim Einschalten des Schützes.")
            else:
                await ctx.send("Modbus client nicht verfügbar.")

        @self.bot.command(name="coil_off")
        async def cmd_coil_off(ctx):
            if self.modbus_client:
                result = await self.modbus_client.write_output(1, False)
                if result:
                    await ctx.send("Schütz ausgeschaltet!")
                else:
                    await ctx.send("Fehler beim Ausschalten des Schützes.")
            else:
                await ctx.send("Modbus client nicht verfügbar.")

    async def on_ready(self):
        # Wird ausgeführt, wenn der Bot erfolgreich verbunden ist.
        logger.info("Der Bot ist jetzt online")
        # Kanal holen, damit wir später Nachrichten senden können.
        self.channel = self.bot.get_channel(self.channel_id)
        if self.channel:
            await self.channel.send("🟢 Ich bin jetzt online!")
            await self.channel.send(
                "Hier eine Liste der gültigen Befehle:"
                f"\n{self.command_prefix}ping - Testet die Verbindung zum Bot"
                f"\n{self.command_prefix}led_on - Schaltet die LED ein"
                f"\n{self.command_prefix}led_off - Schaltet die LED aus"
                f"\n{self.command_prefix}coil_on - Schaltet das Schütz ein"
                f"\n{self.command_prefix}coil_off - Schaltet das Schütz aus"
            )
        else:
            logger.warning(f"Kanal {self.channel_id} nicht gefunden")

    async def notify_input_change(self, input_bit: int, state: bool):
        # Diese Funktion wird vom Modbus-Client aufgerufen, wenn sich ein Eingang ändert.
        try:
            channel = self.channel or self.bot.get_channel(self.channel_id)
            if channel:
                if input_bit == 0:
                    # Eingang 0 ist der Taster. Wir reagieren hier nur auf steigende Flanke.
                    if self.previous_input_state is False and state is True:
                        self.led_state = not self.led_state
                        # LED schalten und Ergebnis prüfen.
                        result = await self.modbus_client.write_output(0, self.led_state)
                        if result:
                            await channel.send(
                                f"LED {'eingeschaltet' if self.led_state else 'ausgeschaltet'} durch Taster!"
                            )
                        else:
                            await channel.send("Fehler beim Schalten der LED durch Taster.")
                    # Zustand merken, damit wir das nächste Mal die Flanke erkennen.
                    self.previous_input_state = state
                else:
                    # Für andere Eingänge nur eine einfache Statusmeldung senden.
                    await channel.send(
                        f"Digitaler Eingang {input_bit} hat sich geändert: {'AN' if state else 'AUS'}"
                    )
            else:
                logger.warning("Kein Kanal verfügbar für Input-Change-Benachrichtigung")
        except Exception as err:
            logger.error(f"Error in notify_input_change: {err}")

    async def discord_bot_task(self):
        # Der Bot wird gestartet und läuft im eigenen asynchronen Kontext.
        # Kontext bedeutet hier die Umgebung, in der der Bot läuft. Das "async with" sorgt dafür, 
        # dass der Bot korrekt gestartet und gestoppt wird, auch wenn es zu Fehlern kommt.
        try:
            async with self.bot:
                await self.bot.start(self.token)
        except Exception as err:
            logger.error(f"Error in Discord bot task: {err}")

    async def stop(self):
        # Bot schließen, wenn das Programm beendet wird.
        logger.info("Der Bot ist jetzt offline")
        await self.bot.close()
