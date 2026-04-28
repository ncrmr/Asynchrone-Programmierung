import asyncio
import logging

from pymodbus import client
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)


class ModbusClient:

    def __init__(self, host: str, port: int):
        # Modbus-Verbindungseinstellungen speichern.
        self.host = host
        self.port = port

        self.client = None
        self.connected = False
        # Ausgänge als virtuelles Abbild speichern.
        self.output_states = {}
        self.input_change_callback = None
        self.previous_input_state = None

        # Basisadressen für Eingänge und Ausgänge im Modbus-Gerät.
        self.input_base = 0x0000   # Adresse der digitalen Eingänge.
        self.output_base = 0x0800  # Adresse der digitalen Ausgänge.
        self.watchdog_disable_register = 0x1120

    async def connect(self) -> bool:
        # Asynchrone Verbindung zum Modbus-Gerät aufbauen.
        if not self.connected:
            try:
                # Instanz des asynchronen Modbus-TCP-Clients erstellen.
                self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

                if await self.client.connect():
                    self.connected = True
                    logger.info(f"Connected to Modbus client at {self.host}:{self.port}")
                    # Nach dem Verbinden den Watchdog deaktivieren.
                    # Nicht empfohlen, hier aber aus Problemen damit deaktiviert
                    # Bei echter Anwendung sollte dieser Codeteil überdacht werden.
                    await self.disable_watchdog()
                    return True
                else:
                    raise ModbusException("Connection failed")

            except Exception as err:
                logger.error(f"Failed to connect to Modbus client: {err}")
                self.connected = False
                return False
        else:
            logger.info("Already connected to Modbus client")
            return True

    async def disconnect(self) -> bool:
        # Verbindung wieder trennen.
        if self.connected:
            try:
                # Modbus-Client sauber schließen. Bei AsyncModbusTcpClient ist close() asynchron.
                close_result = self.client.close()
                # Da close() möglicherweise eine Coroutine zurückgibt, müssen wir prüfen, ob wir darauf warten müssen.
                if asyncio.iscoroutine(close_result):
                    await close_result
                self.connected = False
                logger.info("Disconnected from Modbus client")
                return True
            except Exception as err:
                logger.error(f"Error disconnecting from Modbus client: {err}")
                return False
        else:
            logger.info("Already disconnected from Modbus client")
            return True

    def set_input_change_callback(self, callback):
        # Callback speichern, das bei Eingangssignaländerung ausgeführt wird.
        self.input_change_callback = callback

    async def disable_watchdog(self):
        # Watchdog deaktivieren, damit das Gerät nicht automatisch stoppt. (siehe Kommentar bei Aufruf der Funktion)
        try:
            result = await asyncio.wait_for(
                # Register zum deaktivieren des Watchdogs mit 0 beschreiben. Je nach Gerät könnte das anders sein.
                self.client.write_register(address=self.watchdog_disable_register, value=0, device_id=1),
                # Timeout, um zu verhindern, dass das Programm ewig hängt, wenn das Gerät nicht reagiert.
                timeout=5.0
            )
            if result.isError():
                logger.warning(f"Failed to disable watchdog: {result}")
            else:
                logger.info("Watchdog disabled")
        except Exception as err:
            logger.warning(f"Error disabling watchdog: {err}")

    async def read_input(self, input_bit: int = 0):
        # Einen digitalen Eingang lesen.
        if not self.connected:
            logger.warning("Cannot read inputs - Modbus client not connected")
            return None
        try:
            address = self.input_base + input_bit
            result = await asyncio.wait_for(
                self.client.read_discrete_inputs(address=address, count=1, device_id=1),
                timeout=5.0
            )
            if result.isError():
                logger.error(f"Error reading inputs: {result}")
                return None

            return bool(result.bits[0])

        except asyncio.TimeoutError:
            logger.error("Timeout reading inputs")
            self.connected = False
            return None
        except Exception as err:
            logger.error(f"Error reading inputs: {err}")
            self.connected = False
            return None

    def _build_output_word(self) -> int:
        # Ausgänge in ein Registerwort umwandeln.
        value = 0
        for bit, state in self.output_states.items():
            if state:
                value |= 1 << bit
        return value

    async def _write_output_word(self) -> bool:
        # Das gesamte Ausgangswort an den Modbus Clienten senden.
        address = self.output_base
        # schreiben des Ausgangsabbildes
        value = self._build_output_word()
        result = await asyncio.wait_for(
            # Register der entsprechenden Ausgangskarte mit dem berechneten Wert beschreiben. Je nach Gerät könnte das anders sein.
            self.client.write_register(address=address, value=value, device_id=1),
            # Timeout, um zu verhindern, dass das Programm ewig hängt, wenn das Gerät nicht reagiert.
            timeout=5.0
        )
        if result.isError():
            logger.error(f"Error writing outputs: {result}")
            return False
        return True

    async def write_output(self, output_bit: int = 0, val: bool = False):
        # Einen einzelnen Ausgang im Speicher setzen und dann die ganze Ausgabe schreiben.
        if not self.connected:
            logger.warning("Cannot write outputs - Modbus client not connected")
            return None
        # Ausgangsbit im internen Abbild setzen.
        self.output_states[output_bit] = val

        try:
            # Das gesamte Ausgangsbild an den Modbus Clienten senden.
            success = await self._write_output_word()
            return success

        except asyncio.TimeoutError: # Wenn das Schreiben zu lange dauert, Fehler loggen und Verbindung als verloren markieren.
            logger.error("Timeout writing outputs")
            self.connected = False
            return None
        except Exception as err:
            logger.error(f"Error writing outputs: {err}")
            self.connected = False
            return None

    async def modbus_client_task(self, interval: float = 0.05):
        # Langer Task, der ständig den Modbus-Zustand prüft und Eingänge liest.

        try:
            while True:
                if not self.connected:
                    logger.info("Attempting to reconnect to Modbus client...")
                    await self.connect()

                if self.connected:
                    # Eingangsbit 0 regelmäßig lesen.
                    current_input = await self.read_input(0)
                    if current_input is None:
                        logger.warning("Ping failed, connection may be lost")
                    else:
                        if self.previous_input_state is None:
                            # Erster Zyklus: Zustand merken, aber noch nichts melden.
                            self.previous_input_state = current_input
                        elif self.previous_input_state != current_input:
                            # Zustand hat sich geändert, Callback informieren.
                            #logger.info(f"Digital input 0 changed to {current_input}")
                            self.previous_input_state = current_input
                            if self.input_change_callback:
                                await self.input_change_callback(0, current_input)

                    # Ausgangsbild zyklisch schreiben, damit vorherige Ausgänge nicht verloren gehen.
                    write_result = await self._write_output_word()
                    if not write_result:
                        logger.warning("Failed to maintain output image")
                # Kurze Pause, damit die CPU nicht 100% auslastet. Je nach Anwendungsfall könnte das angepasst werden.
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            # Wenn der Task gestoppt wird, sauber trennen.
            logger.info("Modbus client task cancelled")
            await self.disconnect()

        except Exception as err:
            logger.error(f"Unexpected error in modbus_client_task: {err}")
            await self.disconnect()
        