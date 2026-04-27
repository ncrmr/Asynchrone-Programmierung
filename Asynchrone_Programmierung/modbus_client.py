import asyncio
import logging

from pymodbus import client
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)

class ModbusClient:

    def __init__(self, host:str, port: int, input_count: int = 8, output_count: int = 8):
        self.host = host
        self.port = port

        self.client = None
        self.connected = False
        self.output_states = {}  # Store current output states
        self.input_change_callback = None
        self.previous_input_state = None

        self.input_base = 0x0000   # Prozessdaten-Interface Eingänge
        self.output_base = 0x0800  # Prozessdaten-Interface Ausgänge
        self.watchdog_disable_register = 0x1120

    async def connect(self) -> bool:
        # Connect to Modbus client
        if not self.connected:
            try:
                self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

                if await self.client.connect():
                    self.connected = True
                    logger.info(f"Connected to Modbus client at {self.host}:{self.port}")
                    # Disable watchdog by writing 0 to 0x1120
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
        # Disconnect from Modbus client
        if self.connected:
            try:
                close_result = self.client.close()
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
        self.input_change_callback = callback

    async def disable_watchdog(self):
        # Disable watchdog by writing 0 to register 0x1120
        try:
            result = await asyncio.wait_for(
                self.client.write_register(address=self.watchdog_disable_register, value=0, device_id=1),
                timeout=5.0
            )
            if result.isError():
                logger.warning(f"Failed to disable watchdog: {result}")
            else:
                logger.info("Watchdog disabled")
        except Exception as err:
            logger.warning(f"Error disabling watchdog: {err}")

    async def read_input(self, input_bit: int = 0):
        # Read input states from Modbus client
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
        
    async def write_output(self, output_bit: int = 0, val: bool = False):
        # Write a single output state to Modbus client
        if not self.connected:
            logger.warning("Cannot write outputs - Modbus client not connected")
            return None
        try:
            address = self.output_base + output_bit
            value = 1 if val else 0
            result = await asyncio.wait_for(
                self.client.write_register(address=address, value=value, device_id=1),
                timeout=5.0
            )
            if result.isError():
                logger.error(f"Error writing outputs: {result}")
                return None
            
            self.output_states[output_bit] = val  # Store the state
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout writing outputs")
            self.connected = False
            return None
        except Exception as err:
            logger.error(f"Error writing outputs: {err}")
            self.connected = False
            return None
        
    async def modbus_client_task(self, interval: float = 1.0):
        # Continuous task for monitoring Modbus connection and reading inputs
        await self.connect()
        
        try:
            while True:
                if not self.connected:
                    logger.info("Attempting to reconnect to Modbus client...")
                    await self.connect()
                
                if self.connected:
                    # Read the first digital input and detect changes
                    current_input = await self.read_input(0)
                    if current_input is None:
                        logger.warning("Ping failed, connection may be lost")
                    else:
                        if self.previous_input_state is None:
                            self.previous_input_state = current_input
                        elif self.previous_input_state != current_input:
                            logger.info(f"Digital input 0 changed to {current_input}")
                            self.previous_input_state = current_input
                            if self.input_change_callback:
                                await self.input_change_callback(0, current_input)
                    
                    # Write all stored output states cyclically to maintain them
                    for bit, state in self.output_states.items():
                        write_result = await self.write_output(bit, state)
                        if write_result is None:
                            logger.warning(f"Failed to maintain output {bit}")
                
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            logger.info("Modbus client task cancelled")
            await self.disconnect()
        
        except Exception as err:
            logger.error(f"Unexpected error in modbus_client_task: {err}")
            await self.disconnect()
        