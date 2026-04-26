import asyncio
import logging
import sys

import config
from discord_bot import DiscordBotHandler
from modbus_client import ModbusClient

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

class AsyncSystem:

    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.modbus_client = ModbusClient(
            host = config.MODBUS_HOST,
            port = config.MODBUS_PORT,
            input_count = config.INPUT_COUNT,
            output_count = config.OUTPUT_COUNT
        )
        self.discord_bot = DiscordBotHandler(
            token = config.DISCORD_TOKEN
        )
        self.tasks = []
        self.running = False

    async def run(self):
        logger.info("=" * 60)
        logger.info("Starting Async Modbus-Discord Communication")
        logger.info("=" * 60)

        self.running = True

        try:
            modbus_task = asyncio.create_task(
                self.modbus_client.modbus_client_task(),
                name = "modbus_client"
            )
            discord_task = asyncio.create_task(
                self.discord_bot.discord_bot_task(),
                name = "discord_bot"
            )

            self.tasks = [modbus_task, discord_task]

            logger.info("All tasks started successfully")
            logger.info("System running. Press Ctrl+C to stop.")

            await asyncio.gather(*self.tasks, return_exceptions = True)

        except KeyboardInterrupt:  # Shutdown via Strg+C
            logger.info("Keyboard interrupt received")
        except asyncio.CancelledError:
            logger.info("System cancelled")
        except Exception as err:
            logger.error(f"Unexpected error in main loop: {err}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Shutting down system")
        self.running = False

        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout = 5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Task {task.get_name()} did not stop in time")
                except asyncio.CancelledError:
                    pass

        self.modbus_client.stop()
        await self.modbus_client.disconnect()

        await self.discord_bot.stop()

        logger.info("=" * 60)
        logger.info("System shutdown complete")
        logger.info("=" * 60)

    async def main():
        system = AsyncSystem()


