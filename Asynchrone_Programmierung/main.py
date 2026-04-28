import asyncio # Bibliotehk für asynchrone Programmierung
import logging # Bibliothek für Logging, damit wir sehen können, was im Programm passiert
import sys # Bibliothek für Systemfunktionen, hier z.B. um Log-Ausgaben auf die Konsole zu bringen

import config
from discord_bot import DiscordBotHandler
from modbus_client import ModbusClient

# Logging einrichten: Das hilft beim Debuggen und zeigt später, was das Programm macht.
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

# Logger-Instanz für dieses Modul erstellen.
logger = logging.getLogger(__name__)

class AsyncSystem:

    def __init__(self):
        # Warteschlange für Ereignisse, falls sich später mehrere Komponenten koordinieren müssen.
        self.event_queue = asyncio.Queue()

        # Modbus-Client für die Kommunikation mit der Hardware.
        self.modbus_client = ModbusClient(
            host=config.MODBUS_HOST,
            port=config.MODBUS_PORT,
        )

        # Discord-Bot für Nachrichten im Chat.
        self.discord_bot = DiscordBotHandler(
            token=config.DISCORD_TOKEN,
            channel=config.DISCORD_CHANNEL,
            command_prefix=config.DISCORD_COMMAND_PREFIX,
            modbus_client=self.modbus_client,
        )

        # Callback verbinden: Wenn sich der Eingang ändert, informiert der Bot den Discord-Channel.
        # Callback ... Eine Funktion, die aufgerufen wird, wenn ein bestimmtes Ereignis eintritt.
        self.modbus_client.set_input_change_callback(self.discord_bot.notify_input_change)

        # Liste aller laufenden Aufgaben (Tasks) im Programm.
        self.tasks = []
        self.running = False

    async def run(self):
        # Systemstart melden.
        logger.info("=" * 60)
        logger.info("Starting Async Modbus-Discord Communication")
        logger.info("=" * 60)

        self.running = True

        try:
            # Zwei asynchrone Tasks starten.
            modbus_task = asyncio.create_task(
                self.modbus_client.modbus_client_task(),
                name="modbus_client"
            )
            discord_task = asyncio.create_task(
                self.discord_bot.discord_bot_task(),
                name="discord_bot"
            )

            # Beide Tasks in einer Liste speichern, damit wir sie später beenden können.
            self.tasks = [modbus_task, discord_task]

            logger.info("All tasks started successfully")
            logger.info("System running. Press Ctrl+C to stop.")

            # asyncio.gather wartet auf beide Tasks gleichzeitig.
            # Das heißt das Programm bleibt hier, bis beide Tasks entweder fertig sind oder ein Fehler auftritt.
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except KeyboardInterrupt:  # Wenn der Benutzer Strg+C drückt.
            logger.info("Keyboard interrupt received")
        except asyncio.CancelledError: # Wenn eine Task explizit abgebrochen wird.
            logger.info("System cancelled")
        except Exception as err:
            # Alle anderen Fehler hier abfangen.
            logger.error(f"Unexpected error in main loop: {err}")
        finally:
            # Beim Beenden sauber herunterfahren.
            await self.shutdown()

    async def shutdown(self):
        # Sauberes Herunterfahren der asynchronen Tasks und Verbindungen.
        logger.info("Shutting down system")
        self.running = False

        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    # Kurzes Timeout, damit das Programm nicht ewig hängt.
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Task {task.get_name()} did not stop in time")
                except asyncio.CancelledError:
                    pass

        # Modbus-Verbindung beenden.
        self.modbus_client.stop()
        await self.modbus_client.disconnect()

        # Discord-Bot stoppen.
        await self.discord_bot.stop()

        logger.info("=" * 60)
        logger.info("System shutdown complete")
        logger.info("=" * 60)


async def main():
    # Einstiegspunkt des Programms: AsyncSystem erstellen und starten.
    # Diese ist die Hauptfunktion, die alle Komponenten initialisiert und die Tasks startet.
    system = AsyncSystem()
    await system.run()

# Wenn dieses Skript direkt ausgeführt wird, startet die main-Funktion.
if __name__ == "__main__":
    # asyncio.run startet die asynchrone Hauptfunktion. Sie kümmert sich um die Erstellung und Verwaltung der Event-Schleife.
    asyncio.run(main())


