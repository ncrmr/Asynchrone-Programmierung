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

    async def connect(self) -> bool:
        # Connect to Modbus client
        if not self.connected:
            try:
                self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

                if await self.client.connect():
                    self.connected = True
                    logger.info(f"Connected to Modbus client at {self.host}:{self.port}")
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
                await self.client.close()
                self.connected = False
                logger.info("Disconnected from Modbus client")
                return True
            
            except Exception as err:
                logger.error(f"Error disconnecting from Modbus client: {err}")
                return False
        else:
            logger.info("Already disconnected from Modbus client")
            return True

    async def read_input(self, input_bit: int = 0):
        # Read input states from Modbus client
        if not self.connected:
            logger.warning("Cannot read inputs - Modbus client not connected")
            return None
        try:
            result = await self.client.read_discrete_inputs(address = input_bit, count = 1, device_id = 1)
            if result.isError():
                logger.error(f"Error reading inputs: {results}")
                return None

            return bool(result.bits[input_bit])
        
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
            result = await self.client.write_coil(address = output_bit, value = val, device_id = 1)
            if result.isError():
                logger.error(f"Error writing outputs: {result}")
                return None
            
            return True
            
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
                   pass
                
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            logger.info("Modbus client task cancelled")
            await self.disconnect()
        
        except Exception as err:
            logger.error(f"Unexpected error in modbus_client_task: {err}")
            await self.disconnect()
        