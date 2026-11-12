import time
import collections
import csv
import constants

class SessionData:
    def __init__(self):
        self.reset_all()

    def reset_buffers(self):
        self.time_soc = collections.deque(maxlen=constants.MAX_DATAPOINTS)
        self.soc_data = collections.defaultdict(lambda: collections.deque(maxlen=constants.MAX_DATAPOINTS))
        self.time_pwr = collections.deque(maxlen=constants.MAX_DATAPOINTS)
        self.voltage_data = collections.deque(maxlen=constants.MAX_DATAPOINTS)
        self.current_data = collections.deque(maxlen=constants.MAX_DATAPOINTS)

    def resize_buffers(self):
        self.time_soc = collections.deque(self.time_soc, maxlen=constants.MAX_DATAPOINTS)
        self.time_pwr = collections.deque(self.time_pwr, maxlen=constants.MAX_DATAPOINTS)
        self.voltage_data = collections.deque(self.voltage_data, maxlen=constants.MAX_DATAPOINTS)
        self.current_data = collections.deque(self.current_data, maxlen=constants.MAX_DATAPOINTS)
        for cid in self.soc_data:
            self.soc_data[cid] = collections.deque(self.soc_data[cid], maxlen=constants.MAX_DATAPOINTS)
        self.soc_data.default_factory = lambda: collections.deque(maxlen=constants.MAX_DATAPOINTS)

    def reset_all(self):
        self.start_time = time.time()
        self.reset_buffers()

    def append_soc(self, cell_data_list):
        self.time_soc.append(time.time() - self.start_time)
        for data in cell_data_list:
            self.soc_data[data['id']].append(data['soc'])

    def append_power(self, power_data_list):
        if not power_data_list: return
        self.time_pwr.append(time.time() - self.start_time)
        self.voltage_data.append(power_data_list[0]['voltage'])
        self.current_data.append(power_data_list[0]['current'])

    def export_soc_csv(self, path):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            cell_ids = sorted(list(self.soc_data.keys()))
            writer.writerow(['Time (s)'] + [f'Module {cid} SOC (%)' for cid in cell_ids])
            for i, t in enumerate(self.time_soc):
                row = [t]
                for cid in cell_ids:
                    row.append(self.soc_data[cid][i] if i < len(self.soc_data[cid]) else "")
                writer.writerow(row)

    def export_pwr_csv(self, path, unit_mode):
        mult = 1 if unit_mode == "mV/mA" else 1000.0
        v_head = 'Voltage (mV)' if mult == 1 else 'Voltage (V)'
        c_head = 'Current (mA)' if mult == 1 else 'Current (A)'
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time (s)', v_head, c_head])
            for i, t in enumerate(self.time_pwr):
                v = self.voltage_data[i] / mult if i < len(self.voltage_data) else ""
                c = self.current_data[i] / mult if i < len(self.current_data) else ""
                writer.writerow([t, v, c])