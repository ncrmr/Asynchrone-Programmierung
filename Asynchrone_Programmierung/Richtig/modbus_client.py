import asyncio
import logging

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)

class ModbusClient:

    def __init__(self, host:str, port: int, input_count: int = 8, output_count: int = 8):
        self.host = host
        self.port = port
        self.input_count = input_count
        self.output_count = output_count

        self.input_start = 0
        self.input_count = input_count
        self.output_start = 0
        self.output_count = output_count

        self.client = AsyncModbusTcpClient(host=host, port=port)
        self.connected = False

    async def connect(self) -> bool:
        # Connect to Modbus client
        if not self.connected:
            try:
                if await self.client.connect():
                    self.connected = True
                    logger.info(f"Connected to Modbus client at {self.host}:{self.port}")
                    await self.read_inputs()
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
        
    async def ensure_connected(self) -> bool:
        pass

    async def read_inputs(self):
        # Read input states from Modbus client
        if not self.connected:
            logger.warning("Cannot read inputs - Modbus client not connected")
            return None
        try:
            result = await self.client.read_coils(self.input_start, self.input_count, slave = 1)
            if result.isError():
                logger.error(f"Error reading inputs: {results}")
                return None

            input_states = list(result.bits[:self.input_count])
            return input_states
        
        except Exception as err:
            logger.error(f"Error reading inputs: {err}")
            self.connected = False
            return None
        
    async def write_outputs(self, output_states:list):
        # Write output states to Modbus client
        if not self.connected:
            logger.warning("Cannot write outputs - Modbus client not connected")
            return None
        try:
            result = await self.client.write_coils(self.output_start, output_states, slave = 1)
            if result.isError():
                logger.error(f"Error writing outputs: {result}")
                return None
            
            return output_states
            
        except Exception as err:
            logger.error(f"Error writing outputs: {err}")
            self.connected = False
            return None
        

        