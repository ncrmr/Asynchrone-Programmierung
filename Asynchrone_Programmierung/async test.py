import asyncio
import logging

from pymodbus import client
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusClient:

    def __init__(self, host:str, port: int):
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
                    print("Connected")
                    self.connected = True
                    return True
                else:
                    raise ModbusException("Connection failed")
        
            except Exception as err:
                print("Connection error")
                self.connected = False
                return False

        else:
            return True
        
    async def read_input(self, input_bit: int = 0):
        # Read input states from Modbus client
        if not self.connected:
            return None
        try:
            result = await self.client.read_discrete_inputs(address = input_bit, count = 1, device_id = 1)
            if result.isError():
                return None
            
            return bool(result.bits[input_bit])
        
        except Exception as err:
            print(f"Read error: {err}")
            self.connected = False
            return None
        
    async def write_output(self, output_bit: int = 0, val: bool = False):
        # Write output states to Modbus client
        if not self.connected:
            return None
        try:
            result = await self.client.write_coil(address = output_bit, value = val, device_id = 1)
            if result.isError():
                print(result)
                print("Writing error")
                return False
            
            return True
            
        except Exception as err:
            print("Write error")
            self.connected = False
            return None

async def main():     
    bk9000 = ModbusClient(host = "192.168.0.7", port = 502)
    await bk9000.connect()
    await bk9000.write_output(output_bit=0, val=True)
    while True:
        result = await bk9000.read_input(input_bit = 0)
        print(result)
    
if __name__ == "__main__":
    asyncio.run(main())
