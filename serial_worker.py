import struct
import serial
from PyQt6.QtCore import QThread, pyqtSignal
import constants

class SerialReader(QThread):
    log_signal = pyqtSignal(str)
    ack_signal = pyqtSignal(int)
    heartbeat_signal = pyqtSignal()
    disconnect_signal = pyqtSignal(str) 
    
    cell_data_signal = pyqtSignal(list)
    config_data_signal = pyqtSignal(list) 
    power_data_signal = pyqtSignal(list)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        self.current_num_cells = 0

    def run(self):
        while self.running and self.serial_port.is_open:
            try:
                b = self.serial_port.read(1)
                if not b or b[0] != constants.SYNC_1: continue
                b = self.serial_port.read(1)
                if not b or b[0] != constants.SYNC_2: continue

                header_meta = self.serial_port.read(2)
                if len(header_meta) < 2: continue
                msg_type, payload_length = header_meta[0], header_meta[1]

                body = self.serial_port.read(payload_length + 1)
                if len(body) < (payload_length + 1): continue

                payload = body[:payload_length]
                received_crc = body[payload_length]

                raw_packet = bytes([constants.SYNC_1, constants.SYNC_2, msg_type, payload_length]) + payload
                if constants.xor_checksum(raw_packet) != received_crc:
                    self.log_signal.emit(f"[Warning] CRC Mismatch on msg 0x{msg_type:02X}")
                    continue

                self.heartbeat_signal.emit()
                self.parse_message(msg_type, payload)

            except serial.SerialException as e:
                if self.running:
                    self.disconnect_signal.emit(f"Hardware disconnected: {str(e)}")
                    self.running = False
            except Exception as e:
                if self.running:
                    self.log_signal.emit(f"Serial Read Error: {str(e)}")
                    self.running = False

    def parse_message(self, msg_type, payload):
        if msg_type == constants.MSG_TYPE_ACK:
            if len(payload) == 1:
                self.ack_signal.emit(payload[0])
                
        elif msg_type == constants.MSG_TYPE_CELL_INFO:
            num_cells = len(payload) // constants.CELL_SIZE
            self.current_num_cells = num_cells
            
            cell_data_list = []
            log_str = f"--- Received {num_cells} Cells ---\n"
            
            for i in range(num_cells):
                chunk = payload[i * constants.CELL_SIZE : (i + 1) * constants.CELL_SIZE]
                status, vol, soc = struct.unpack(constants.CELL_FMT, chunk)
                
                status_map = {0: "OK", 1: "CAL_UNAV", 0xF0: "NO_DETECT", 0xF1: "DISCONN", 0xF2: "UPD_FAIL"}
                s_str = status_map.get(status, f"UNK({status})")
                log_str += f"  Cell {i+1}: {vol}mV | {soc}% | {s_str}\n"
                
                cell_data_list.append({
                    "id": i + 1, "voltage": vol, "soc": soc, "status": s_str
                })
                
            self.log_signal.emit(log_str.strip())
            self.cell_data_signal.emit(cell_data_list)

        elif msg_type == constants.MSG_TYPE_BATTERY_CONFIG:
            # We must know the cell count from MSG_TYPE_CELL_INFO to decode this structurally
            if self.current_num_cells == 0: return
            
            config_size = self.current_num_cells + 6
            num_configs = len(payload) // config_size
            
            if num_configs == 0: return
            
            config_fmt = f"<{self.current_num_cells}B3H"
            config_data_list = []
            log_str = f"--- Received {num_configs} Battery Configs ---\n"
            state_map = {0: "B", 1: "P", 2: "N", 3: "V"}
            
            for i in range(num_configs):
                chunk = payload[i * config_size : (i + 1) * config_size]
                unpacked_data = struct.unpack(config_fmt, chunk)
                
                states = unpacked_data[:self.current_num_cells]
                min_v, max_v, base_v = unpacked_data[-3:]
                state_strs = [state_map.get(s, "?") for s in states]
                log_str += f"  Config {i+1}: Min={min_v}mV | Max={max_v}mV | States={'-'.join(state_strs)}\n"
                
                config_data_list.append({
                    "id": i + 1, "min_v": min_v, "max_v": max_v, "states": state_strs
                })
                
            self.log_signal.emit(log_str.strip())
            self.config_data_signal.emit(config_data_list)

        elif msg_type == constants.MSG_TYPE_POWER_INFO:
            num_items = len(payload) // constants.POWER_SIZE
            power_data_list = []
            log_str = f"--- Received {num_items} Power Info ---\n"
            
            for i in range(num_items):
                chunk = payload[i * constants.POWER_SIZE : (i + 1) * constants.POWER_SIZE]
                vol, cur = struct.unpack(constants.POWER_FMT, chunk)
                log_str += f"  Power {i+1}: {vol}mV | {cur}mA\n"
                power_data_list.append({"voltage": vol, "current": cur})
                
            self.log_signal.emit(log_str.strip())
            self.power_data_signal.emit(power_data_list)