import struct
import constants

class ProtocolError(Exception): pass

def build_bms_command(mode_str, curr_txt, volt_txt, amp_txt, freq_txt, unit_mode):
    mult = 1 if unit_mode == "mV/mA" else 1000.0
    mode, submode, param_1, param_2 = 0, 0, 0, 0
    settings_str = ""

    try:
        if mode_str == "OFF":
            mode = 0
            settings_str = "OFF Mode"
        elif mode_str == "CHARGING":
            mode = 1
            param_1 = int(float(curr_txt.replace(',', '.') or "0") * mult)
            if not (0 <= param_1 <= constants.MAX_CURRENT_MA):
                raise ProtocolError(f"Current must be between 0 and {constants.MAX_CURRENT_MA/mult:g}.")
            settings_str = f"CHARGING Mode ({param_1} mA)"
        elif mode_str == "DC":
            mode = 2
            submode = 0
            param_1 = int(float(volt_txt.replace(',', '.') or "0") * mult)
            if not (-constants.MAX_VOLTAGE_MV <= param_1 <= constants.MAX_VOLTAGE_MV):
                raise ProtocolError(f"Voltage must be between {-constants.MAX_VOLTAGE_MV/mult:g} and {constants.MAX_VOLTAGE_MV/mult:g}.")
            settings_str = f"BMS DC Mode ({param_1} mV)"
        elif mode_str == "AC":
            mode = 2
            submode = 1
            param_1 = int(float(amp_txt.replace(',', '.') or "0") * mult)
            param_2 = int(freq_txt or "0")
            if not (0 <= param_1 <= constants.MAX_VOLTAGE_MV):
                raise ProtocolError(f"Amplitude must be between 0 and {constants.MAX_VOLTAGE_MV/mult:g}.")
            if not (constants.MIN_FREQ_HZ <= param_2 <= constants.MAX_FREQ_HZ):
                raise ProtocolError(f"Frequency must be between {constants.MIN_FREQ_HZ} and {constants.MAX_FREQ_HZ} Hz.")
            settings_str = f"BMS AC Mode (Amp: {param_1}, Freq: {param_2} Hz)"

        payload = struct.pack(constants.CMD_FMT, mode, submode, param_1, param_2)
        header = bytes([constants.SYNC_1, constants.SYNC_2, constants.MSG_TYPE_PC_COMMAND, len(payload)])
        crc = constants.xor_checksum(header + payload)
        
        return header + payload + bytes([crc]), mode, submode, param_1, param_2, settings_str

    except ValueError:
        raise ProtocolError("Please ensure all required parameters contain valid numbers.")