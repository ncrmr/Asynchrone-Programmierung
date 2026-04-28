import logging

#################################################################
# Modbus-Konfiguration
#################################################################

# IP-Adresse der Modbus-Geräte für die Verbindung.
MODBUS_HOST = "192.168.0.7"
# Port als String, weil manche Settings-Dateien das so erwarten.
MODBUS_PORT = "502"

#################################################################
# Discord-Konfiguration
#################################################################

# Discord-Token, das vom Bot beim Start verwendet wird.
DISCORD_TOKEN_PART_A = "MTQ5NjkzNjU5OTQ3OTM5MDM3MQ.G0EWMw."
DISCORD_TOKEN_PART_B = "VXuTQdAPgou3btyp_DomzA1szjfJvJgzLeDlqo"
DISCORD_TOKEN = DISCORD_TOKEN_PART_A + DISCORD_TOKEN_PART_B
# ID des Discord-Channels, in den der Bot schreibt.
DISCORD_CHANNEL = 1496938937334108333
# Präfix für Discord-Befehle, hier z. B. !led_on
DISCORD_COMMAND_PREFIX = "!"

#################################################################
# Logging-Konfiguration
#################################################################

# Welche Meldungen geloggt werden sollen.
LOG_LEVEL = logging.INFO
# Format der Logausgaben mit Zeit, Modulname und Schweregrad.
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# Name der Logdatei, in die geschrieben wird.
LOG_FILE = "async_system.log"