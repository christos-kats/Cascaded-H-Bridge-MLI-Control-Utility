import struct

# --- Global Hardware Limits & Settings ---
MAX_CURRENT_MA = 10000   
MAX_VOLTAGE_MV = 60000   
MIN_FREQ_HZ    = 1       
MAX_FREQ_HZ    = 1000    

# Dynamic Array Limits
MAX_DATAPOINTS = 60 

# System Timers
INACTIVITY_TIMEOUT_MS = 3000 
ACK_TIMEOUT_MS        = 2000
GRAPH_UPDATE_MS       = 500

# --- Protocol Definitions ---
SYNC_1 = 0xAA
SYNC_2 = 0xBB

MSG_TYPE_CELL_INFO      = 0x10
MSG_TYPE_BATTERY_CONFIG = 0x20
MSG_TYPE_POWER_INFO     = 0x30
MSG_TYPE_PC_COMMAND     = 0x40
MSG_TYPE_ACK            = 0x50

CMD_FMT = "<BBii"
CELL_FMT = "<BHH"
POWER_FMT = "<ii"

CELL_SIZE = struct.calcsize(CELL_FMT)
POWER_SIZE = struct.calcsize(POWER_FMT)

def xor_checksum(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
    return crc