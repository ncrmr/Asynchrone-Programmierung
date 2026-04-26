import logging

#################################################################
# Modbus configuration
#################################################################

MODBUS_HOST = "192.168.0.7"
MODBUS_PORT = "502"

#################################################################
# Discord configuration
#################################################################

DISCORD_TOKEN_PART_A = "MTQ5NjkzNjU5OTQ3OTM5MDM3MQ.G0EWMw."
DISCORD_TOKEN_PART_B = "VXuTQdAPgou3btyp_DomzA1szjfJvJgzLeDlqo"
DISCORD_TOKEN = DISCORD_TOKEN_PART_A + DISCORD_TOKEN_PART_B
DISCORD_CHANNEL = 1496938937334108333
DISCORD_COMMAND_PREFIX= "!"

#################################################################
# Logging configuration
#################################################################

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "async_system.log"