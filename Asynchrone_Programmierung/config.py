#################################################################
# Modbus configuration
#################################################################

MODBUS_HOST = "192.168.0.7"
MODBUS_PORT = "502"

INPUT_COUNT = 8
OUTPUT_COUNT = 8

#################################################################
# Discord configuration
#################################################################

DISCORD_TOKEN = "MTQ5NjkzNjU5OTQ3OTM5MDM3MQ.GPwW9X.bgO0wJOlr7528VLVn-Ix3HPTXMVqAUujZDbzgM"

DISCORD_COMMAND_PREFIX= "!"


#################################################################
# Logging configuration
#################################################################

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "async_system.log"