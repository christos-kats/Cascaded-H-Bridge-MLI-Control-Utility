import sys
import time
import serial
import serial.tools.list_ports

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QFileDialog, QInputDialog, QCheckBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIntValidator, QDoubleValidator

# --- Local Modules ---
import constants
import settings
import protocol
from ui_main import Ui_MainWindow
from data_store import SessionData
from widgets import HardwareLimitsDialog, GraphSettingsDialog
from serial_worker import SerialReader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_settings = settings.load_settings()
        self.session = SessionData()
        self.serial_port = serial.Serial(baudrate=self.app_settings.get("baudrate", 115200), timeout=1.0)
        self.reader_thread = None
        self.pending_mode = "OFF"
        
        # Build UI & Menus
        self.setWindowTitle("STM32 BMS Control Panel")
        self.resize(1200, 900) 
        self.setMinimumSize(900, 600)
        self.ui = Ui_MainWindow()
        self.ui.setup_ui(self, self.app_settings)
        self.ui.setup_menu(self, self.app_settings)

        # Timers linked to constants
        self.ack_timer = QTimer(singleShot=True)
        self.ack_timer.timeout.connect(self.on_ack_timeout)
        self.heartbeat_timer = QTimer(singleShot=True)
        self.heartbeat_timer.timeout.connect(self.on_heartbeat_timeout)
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(constants.GRAPH_UPDATE_MS)
        
        self.connect_signals()
        self.refresh_ports()
        self.statusBar().showMessage("Disconnected")
        
        # Initialize UI States
        self.toggle_units(self.ui.action_toggle_units.isChecked())
        self.toggle_dark_mode(self.ui.action_dark_mode.isChecked())

    def connect_signals(self):
        # Buttons
        self.ui.btn_refresh.clicked.connect(self.refresh_ports)
        self.ui.btn_connect.clicked.connect(self.toggle_connection)
        self.ui.btn_send.clicked.connect(self.send_command)
        self.ui.btn_clear_console.clicked.connect(self.ui.console.clear)
        
        # Exports
        self.ui.btn_exp_soc_csv.clicked.connect(lambda: self.save_file("Save SOC Data", "CSV Files (*.csv)", self.session.export_soc_csv))
        self.ui.btn_exp_pwr_csv.clicked.connect(lambda: self.save_file("Save Power Data", "CSV Files (*.csv)", lambda p: self.session.export_pwr_csv(p, self.app_settings["unit_mode"])))
        self.ui.btn_exp_soc_png.clicked.connect(lambda: self.save_file("Save SOC Plot", "PNG Files (*.png)", self.ui.soc_graph.export_png))
        self.ui.btn_exp_pwr_png.clicked.connect(lambda: self.save_file("Save Power Plot", "PNG Files (*.png)", self.ui.pwr_graph.export_png))

        # Radio Inputs Logic
        self.ui.radio_off.toggled.connect(self.update_input_states)
        self.ui.radio_charging.toggled.connect(self.update_input_states)
        self.ui.radio_dc.toggled.connect(self.update_input_states)
        self.ui.radio_ac.toggled.connect(self.update_input_states)
        self.update_input_states()

        # UI Events
        self.ui.console.verticalScrollBar().valueChanged.connect(self.on_scrollbar_changed)
        
        # Menus
        self.ui.action_export_all.triggered.connect(self.export_all_csv)
        self.ui.action_save_log.triggered.connect(self.save_console_log)
        self.ui.action_exit.triggered.connect(self.close)
        self.ui.action_baud.triggered.connect(self.change_baud_rate)
        self.ui.action_graph_hist.triggered.connect(self.change_graph_history)
        self.ui.action_hw_limits.triggered.connect(self.change_hardware_limits)
        self.ui.action_expand_all.triggered.connect(lambda: self.toggle_all_groups(True))
        self.ui.action_collapse_all.triggered.connect(lambda: self.toggle_all_groups(False))
        self.ui.action_clear_data.triggered.connect(self.clear_all_data)
        
        # Toggles & Callbacks
        self.ui.action_toggle_units.toggled.connect(self.toggle_units)
        self.ui.action_dark_mode.toggled.connect(self.toggle_dark_mode)
        self.ui.action_show_legends.toggled.connect(self.save_view_settings)
        self.ui.action_show_titles.toggled.connect(self.save_view_settings)
        self.ui.action_show_timestamps.toggled.connect(self.save_view_settings)
        self.ui.action_show_raw.toggled.connect(self.save_view_settings)
        self.ui.action_about.triggered.connect(self.show_about)
        self.ui.action_protocol.triggered.connect(self.show_protocol_details)

    # --- Setup & Visuals ---
    def refresh_ports(self):
        self.ui.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if ports:
            self.ui.port_combo.addItems([p.device for p in ports])
        else:
            self.ui.port_combo.addItem("No ports found")

    def update_input_states(self):
        self.ui.lbl_current.setEnabled(self.ui.radio_charging.isChecked())
        self.ui.input_current.setEnabled(self.ui.radio_charging.isChecked())
        self.ui.lbl_voltage.setEnabled(self.ui.radio_dc.isChecked())
        self.ui.input_voltage.setEnabled(self.ui.radio_dc.isChecked())
        
        is_ac = self.ui.radio_ac.isChecked()
        self.ui.lbl_amp.setEnabled(is_ac)
        self.ui.input_amp.setEnabled(is_ac)
        self.ui.lbl_freq.setEnabled(is_ac)
        self.ui.input_freq.setEnabled(is_ac)

    def on_scrollbar_changed(self, value):
        if not getattr(self, '_auto_scrolling', False):
            scb = self.ui.console.verticalScrollBar()
            self.ui.chk_auto_scroll.setChecked(value >= scb.maximum())

    def log_msg(self, text, color=None):
        if text.startswith("--- Received") and not self.ui.action_show_raw.isChecked():
            return
        if self.app_settings.get("show_timestamps"):
            text = f"{time.strftime('[%H:%M:%S] ')}{text}"
        
        html_text = text if (not color or color == "black") else f'<span style="color:{color};">{text}</span>'
        self.ui.console.append(html_text)
        
        if self.ui.chk_auto_scroll.isChecked():
            self._auto_scrolling = True
            self.ui.console.verticalScrollBar().setValue(self.ui.console.verticalScrollBar().maximum())
            self._auto_scrolling = False

    def show_protocol_details(self):
        details = (
            "<b>Telemetry Packet Structure:</b><br>"
            "[0xAA, 0xBB] [Msg ID] [Payload Len] [Payload Data] [XOR Checksum]<br><br>"
            "<b>Message IDs:</b><br>"
            "0x10 : Cell Info (Volts, SOC, Status)<br>"
            "0x20 : Battery Configuration Array<br>"
            "0x30 : Power Info (Voltage, Current)<br>"
            "0x40 : PC Command (Sent to STM32)<br>"
            "0x50 : STM32 ACK Response"
        )
        QMessageBox.information(self, "Protocol Details", details)

    def show_about(self):
        QMessageBox.information(self, "About", "STM32 BMS Control Panel v1.0\n\nCustom UI for advanced battery management and real-time telemetry monitoring.")

    # --- Preferences Updates ---
    def save_view_settings(self):
        self.app_settings.update({
            "show_legends": self.ui.action_show_legends.isChecked(),
            "show_titles": self.ui.action_show_titles.isChecked(),
            "show_timestamps": self.ui.action_show_timestamps.isChecked(),
            "show_raw_telemetry": self.ui.action_show_raw.isChecked()
        })
        settings.save_settings(self.app_settings)
        self.update_plots()

    def toggle_units(self, checked):
        um = "V/A" if checked else "mV/mA"
        self.app_settings["unit_mode"] = um
        settings.save_settings(self.app_settings)
        
        # 1. Update text validators and table headers
        self.update_labels_and_validators()
        
        # 2. Instantly convert existing table data
        if self.ui.cell_table.rowCount() > 0:
            for row in range(self.ui.cell_table.rowCount()):
                val_item = self.ui.cell_table.item(row, 1)
                if val_item:
                    try:
                        val = float(val_item.text())
                        new_val = val / 1000.0 if checked else val * 1000.0
                        val_item.setText(f"{new_val:.3f}" if checked else f"{int(new_val)}")
                    except ValueError: pass
                    
        if self.ui.config_table.rowCount() > 0:
            for row in range(self.ui.config_table.rowCount()):
                min_item = self.ui.config_table.item(row, 1)
                max_item = self.ui.config_table.item(row, 2)
                if min_item and max_item:
                    try:
                        min_v, max_v = float(min_item.text()), float(max_item.text())
                        new_min = min_v / 1000.0 if checked else min_v * 1000.0
                        new_max = max_v / 1000.0 if checked else max_v * 1000.0
                        min_item.setText(f"{new_min:.3f}" if checked else f"{int(new_min)}")
                        max_item.setText(f"{new_max:.3f}" if checked else f"{int(new_max)}")
                    except ValueError: pass

        # 3. Convert Output Monitor displays
        try:
            curr_v = float(self.ui.lbl_mon_volt.text().split(' ')[0])
            curr_c = float(self.ui.lbl_mon_curr.text().split(' ')[0])
            if checked: # Switched to V/A
                self.ui.lbl_mon_volt.setText(f"{curr_v / 1000.0:.3f} V")
                self.ui.lbl_mon_curr.setText(f"{curr_c / 1000.0:.3f} A")
            else: # Switched to mV/mA
                self.ui.lbl_mon_volt.setText(f"{int(curr_v * 1000.0)} mV")
                self.ui.lbl_mon_curr.setText(f"{int(curr_c * 1000.0)} mA")
        except Exception: pass

        self.log_msg(f"Units switched to {um}", "blue")
        self.update_plots()

    def update_labels_and_validators(self):
        um = self.app_settings["unit_mode"]
        if um == "mV/mA":
            self.ui.lbl_current.setText(f"   Current (0 - {constants.MAX_CURRENT_MA} mA):")
            self.ui.input_current.setValidator(QIntValidator(0, constants.MAX_CURRENT_MA))
            
            self.ui.lbl_voltage.setText(f"   Voltage ({-constants.MAX_VOLTAGE_MV} - {constants.MAX_VOLTAGE_MV} mV):")
            self.ui.input_voltage.setValidator(QIntValidator(-constants.MAX_VOLTAGE_MV, constants.MAX_VOLTAGE_MV))
            
            self.ui.lbl_amp.setText(f"   Amplitude (0 - {constants.MAX_VOLTAGE_MV} mV):")
            self.ui.input_amp.setValidator(QIntValidator(0, constants.MAX_VOLTAGE_MV))
            
            self.ui.cell_table.setHorizontalHeaderLabels(["Module ID", "Voltage (mV)", "SOC (%)", "Status"])
        else:
            self.ui.lbl_current.setText(f"   Current (0 - {constants.MAX_CURRENT_MA/1000:g} A):")
            self.ui.input_current.setValidator(QDoubleValidator(0.0, constants.MAX_CURRENT_MA/1000.0, 3))
            
            self.ui.lbl_voltage.setText(f"   Voltage ({-constants.MAX_VOLTAGE_MV/1000:g} - {constants.MAX_VOLTAGE_MV/1000:g} V):")
            self.ui.input_voltage.setValidator(QDoubleValidator(-constants.MAX_VOLTAGE_MV/1000.0, constants.MAX_VOLTAGE_MV/1000.0, 3))
            
            self.ui.lbl_amp.setText(f"   Amplitude (0 - {constants.MAX_VOLTAGE_MV/1000:g} V):")
            self.ui.input_amp.setValidator(QDoubleValidator(0.0, constants.MAX_VOLTAGE_MV/1000.0, 3))
            
            self.ui.cell_table.setHorizontalHeaderLabels(["Module ID", "Voltage (V)", "SOC (%)", "Status"])
            
        # Dynamically set config headers based on its current column size
        num_cols = self.ui.config_table.columnCount()
        if num_cols >= 3:
            num_states = num_cols - 3
            um_prefix = um.split('/')[0]
            headers = ["ID", f"Min ({um_prefix})", f"Max ({um_prefix})"] + [f"C{i+1}" for i in range(num_states)]
            self.ui.config_table.setHorizontalHeaderLabels(headers)
            
        self.ui.lbl_freq.setText(f"   Frequency ({constants.MIN_FREQ_HZ} - {constants.MAX_FREQ_HZ} Hz):")
        self.ui.input_freq.setValidator(QIntValidator(constants.MIN_FREQ_HZ, constants.MAX_FREQ_HZ))

    def toggle_dark_mode(self, checked):
        self.app_settings["is_dark_mode"] = checked
        settings.save_settings(self.app_settings)
        if checked:
            self.setStyleSheet("""
                QMainWindow, QDialog, QInputDialog { background-color: #2b2b2b; color: #ffffff; }
                QGroupBox, QLabel, QCheckBox, QRadioButton { color: #ffffff; }
                QPushButton { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555; border-radius: 3px; padding: 5px; }
                QPushButton:checked { background-color: #555555; }
                QLineEdit, QTextEdit, QTableWidget, QComboBox { background-color: #1e1e1e; color: #ffffff; border: 1px solid #555555; }
                QListView, QAbstractItemView { background-color: #1e1e1e; color: #ffffff; }
                QHeaderView::section { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555;}
                QMenuBar { background-color: #2b2b2b; color: #ffffff; }
                QMenu { background-color: #2b2b2b; color: #ffffff; }
                QMenu::item:selected { background-color: #555555; }
                QStatusBar { color: #ffffff; }
                QLabel#MonitorTitle { color: #aaaaaa; }
                QLabel#MonitorValue { border: 2px solid #555555; border-radius: 6px; padding: 8px; color: white; background-color: #1e1e1e; }
            """)
        else:
            self.setStyleSheet("""
                QLabel#MonitorTitle { color: #666666; }
                QLabel#MonitorValue { border: 2px solid #cccccc; border-radius: 6px; padding: 8px; color: black; background-color: #f8f9fa; }
            """)
            
        for box in self.ui.collapsible_boxes: box.update_theme(checked)
        self.update_plots()

    def toggle_all_groups(self, expand):
        for box in self.ui.collapsible_boxes:
            if box.toggle_btn.isChecked() != expand:
                box.toggle_btn.setChecked(expand)

    def change_hardware_limits(self):
        dialog = HardwareLimitsDialog(self)
        if dialog.exec():
            constants.MAX_CURRENT_MA = int(dialog.curr.text())
            constants.MAX_VOLTAGE_MV = int(dialog.vmax.text())
            constants.MIN_FREQ_HZ = int(dialog.fmin.text())
            constants.MAX_FREQ_HZ = int(dialog.fmax.text())
            
            constants.INACTIVITY_TIMEOUT_MS = int(dialog.inactivity.text())
            constants.ACK_TIMEOUT_MS = int(dialog.ack.text())
            
            settings.save_settings(self.app_settings)
            self.update_labels_and_validators()
            self.log_msg("Hardware settings updated and saved successfully.", "blue")

    def change_graph_history(self):
        dialog = GraphSettingsDialog(self)
        if dialog.exec():
            dp_val = int(dialog.datapoints.text())
            ms_val = int(dialog.update_ms.text())
            
            constants.MAX_DATAPOINTS = self.app_settings["MAX_DATAPOINTS"] = dp_val
            constants.GRAPH_UPDATE_MS = self.app_settings["GRAPH_UPDATE_MS"] = ms_val
            
            settings.save_settings(self.app_settings)
            
            # Apply changes
            self.session.resize_buffers()
            self.plot_timer.start(constants.GRAPH_UPDATE_MS)
            
            self.log_msg(f"Graph settings updated to {dp_val} points at {ms_val}ms intervals.", "blue")

    def change_baud_rate(self):
        if self.serial_port.is_open:
            QMessageBox.warning(self, "Warning", "Please disconnect before changing the baud rate.")
            return
        rates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        current = str(self.serial_port.baudrate)
        rate, ok = QInputDialog.getItem(self, "Connection Settings", "Select Baud Rate:", rates, rates.index(current) if current in rates else 4, False)
        if ok and rate:
            self.serial_port.baudrate = self.app_settings["baudrate"] = int(rate)
            settings.save_settings(self.app_settings)
            self.log_msg(f"Baud rate changed and saved to {rate}.", "blue")

    # --- Device Communication ---
    def toggle_connection(self):
        if not self.serial_port.is_open:
            port = self.ui.port_combo.currentText()
            if port == "No ports found" or not port: return QMessageBox.warning(self, "Error", "Invalid COM port.")
            try:
                self.serial_port.port = port
                self.serial_port.open()
                self.ui.btn_connect.setText("Disconnect")
                self.ui.btn_send.setEnabled(True)
                self.ui.port_combo.setEnabled(False) 
                self.ui.btn_refresh.setEnabled(False)
                self.session.reset_all()
                self.log_msg(f"Connected to {self.serial_port.port}")
                self.statusBar().showMessage("Connected")
                
                self.reader_thread = SerialReader(self.serial_port)
                self.reader_thread.log_signal.connect(self.log_msg)
                self.reader_thread.ack_signal.connect(self.on_ack_received)
                self.reader_thread.heartbeat_signal.connect(self.on_heartbeat_received)
                self.reader_thread.disconnect_signal.connect(self.handle_hard_disconnect)
                self.reader_thread.cell_data_signal.connect(self.on_telemetry_received)
                self.reader_thread.config_data_signal.connect(self.on_config_received)
                self.reader_thread.power_data_signal.connect(self.on_power_received)
                self.reader_thread.start()
                self.heartbeat_timer.start(constants.INACTIVITY_TIMEOUT_MS)
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
        else:
            self.handle_hard_disconnect("User requested disconnect")

    def handle_hard_disconnect(self, reason):
        self.heartbeat_timer.stop()
        self.ack_timer.stop()
        if self.reader_thread: self.reader_thread.running = False
        try: self.serial_port.close()
        except: pass
        if self.reader_thread and self.reader_thread.isRunning(): self.reader_thread.wait()

        self.ui.btn_connect.setText("Connect")
        self.ui.btn_send.setEnabled(False)
        self.ui.port_combo.setEnabled(True)
        self.ui.btn_refresh.setEnabled(True)
        self.statusBar().showMessage("Disconnected")
        
        if reason.startswith("Device stopped"):
            QMessageBox.warning(self, "Connection Lost", "The device stopped responding (Timeout).")
        self.log_msg(f"[Error] {reason}" if reason != "User requested disconnect" else "Disconnected.", color="red")

    def send_command(self):
        self.pending_mode = "OFF" if self.ui.radio_off.isChecked() else "CHARGING" if self.ui.radio_charging.isChecked() else "DC" if self.ui.radio_dc.isChecked() else "AC"
        try:
            packet, m, sm, p1, p2, info_str = protocol.build_bms_command(
                self.pending_mode, self.ui.input_current.text(), self.ui.input_voltage.text(),
                self.ui.input_amp.text(), self.ui.input_freq.text(), self.app_settings["unit_mode"]
            )
            self.last_sent_settings = info_str
            self.serial_port.write(packet)
            self.log_msg(f">> Sent CMD: Mode={m}, Sub={sm}, P1={p1}, P2={p2}")
            self.ack_timer.start(constants.ACK_TIMEOUT_MS)
        except protocol.ProtocolError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            self.handle_hard_disconnect(f"Write failed: {str(e)}")

    def on_heartbeat_received(self):
        self.heartbeat_timer.start(constants.INACTIVITY_TIMEOUT_MS)
        if self.statusBar().currentMessage() == "Disconnected (Timeout)":
            self.statusBar().showMessage("Connected")
            self.log_msg("Connection restored.", color="green")

    def on_heartbeat_timeout(self):
        self.handle_hard_disconnect("Device stopped responding (Timeout)")
        self.ui.cell_table.setRowCount(0) 
        self.ui.config_table.setRowCount(0)
        self.ui.lbl_mon_volt.setText("0 V" if self.app_settings["unit_mode"] == "V/A" else "0 mV")
        self.ui.lbl_mon_curr.setText("0 A" if self.app_settings["unit_mode"] == "V/A" else "0 mA")

    def on_ack_received(self, mode):
        self.ack_timer.stop()
        self.ui.lbl_mon_mode.setText(self.pending_mode)
        
        msg = f"Settings applied successfully: {self.last_sent_settings}"
        self.log_msg(f"[<<< ACK OK >>>] {msg}", color="green")
        self.statusBar().showMessage(msg)

    def on_ack_timeout(self):
        self.log_msg(f"[!!! TIMEOUT !!!] No ACK from STM32 within {constants.ACK_TIMEOUT_MS/1000} seconds.", color="red")

    # --- Data Receivers & Table Updaters ---
    def format_val(self, val):
        return str(val) if self.app_settings["unit_mode"] == "mV/mA" else f"{val/1000.0:.3f}"

    def on_telemetry_received(self, cell_data):
        if len(self.ui.chk_soc_dict) != len(cell_data):
            for chk in self.ui.chk_soc_dict.values():
                self.ui.soc_chk_container.removeWidget(chk)
                chk.deleteLater()
            self.ui.chk_soc_dict.clear()
            
            for data in cell_data:
                cid = data['id']
                chk = QCheckBox(f"Cell {cid}")
                chk.setChecked(True)
                self.ui.soc_chk_container.addWidget(chk)
                self.ui.chk_soc_dict[cid] = chk
    
        self.session.append_soc(cell_data)
        self.ui.cell_table.setRowCount(len(cell_data))
        for row, data in enumerate(cell_data):
            self.ui.cell_table.setItem(row, 0, QTableWidgetItem(str(data['id'])))
            self.ui.cell_table.setItem(row, 1, QTableWidgetItem(self.format_val(data['voltage'])))
            self.ui.cell_table.setItem(row, 2, QTableWidgetItem(str(data['soc'])))
            self.ui.cell_table.setItem(row, 3, QTableWidgetItem(data['status']))

    def on_config_received(self, config_data):
        if not config_data: return
        num_states = len(config_data[0]['states'])
        
        expected_cols = 3 + num_states
        if self.ui.config_table.columnCount() != expected_cols:
            self.ui.config_table.setColumnCount(expected_cols)
            self.update_labels_and_validators() 

        self.ui.config_table.setRowCount(len(config_data))
        for row, data in enumerate(config_data):
            self.ui.config_table.setItem(row, 0, QTableWidgetItem(str(data['id'])))
            self.ui.config_table.setItem(row, 1, QTableWidgetItem(self.format_val(data['min_v'])))
            self.ui.config_table.setItem(row, 2, QTableWidgetItem(self.format_val(data['max_v'])))
            for i, state in enumerate(data['states']):
                self.ui.config_table.setItem(row, 3 + i, QTableWidgetItem(state))

    def on_power_received(self, power_data):
        self.session.append_power(power_data)
        if power_data:
            v_val = self.format_val(power_data[0]['voltage'])
            c_val = self.format_val(power_data[0]['current'])
            u_v = "V" if self.app_settings["unit_mode"] == "V/A" else "mV"
            u_c = "A" if self.app_settings["unit_mode"] == "V/A" else "mA"
            self.ui.lbl_mon_volt.setText(f"{v_val} {u_v}")
            self.ui.lbl_mon_curr.setText(f"{c_val} {u_c}")

    def update_plots(self):
        dm = self.app_settings["is_dark_mode"]
        st = self.app_settings["show_titles"]
        sl = self.app_settings["show_legends"]
        self.ui.soc_graph.draw_soc(self.session, self.ui.chk_soc_dict, st, sl, dm)
        self.ui.pwr_graph.draw_power(self.session, self.ui.chk_voltage, self.ui.chk_current, self.app_settings["unit_mode"], st, sl, dm)

    # --- Utilities ---
    def save_file(self, title, filter_str, export_func):
        path, _ = QFileDialog.getSaveFileName(self, title, "", filter_str)
        if path:
            try:
                export_func(path)
                self.log_msg(f"Exported successfully to {path}", color="green")
            except Exception as e:
                self.log_msg(f"Export failed: {str(e)}", color="red")

    def export_all_csv(self):
        self.save_file("Save SOC Data", "CSV (*.csv)", self.session.export_soc_csv)
        self.save_file("Save Power Data", "CSV (*.csv)", lambda p: self.session.export_pwr_csv(p, self.app_settings["unit_mode"]))

    def save_console_log(self):
        self.save_file("Save Console Log", "TXT (*.txt)", lambda p: open(p, 'w', encoding='utf-8').write(self.ui.console.toPlainText()))

    def clear_all_data(self):
        self.session.reset_all()
        self.ui.console.clear()
        self.ui.cell_table.setRowCount(0)
        self.ui.config_table.setRowCount(0)
        self.ui.lbl_mon_mode.setText("-")
        self.ui.lbl_mon_volt.setText("0 V" if self.app_settings["unit_mode"] == "V/A" else "0 mV")
        self.ui.lbl_mon_curr.setText("0 A" if self.app_settings["unit_mode"] == "V/A" else "0 mA")
        
        for chk in self.ui.chk_soc_dict.values():
            self.ui.soc_chk_container.removeWidget(chk)
            chk.deleteLater()
        self.ui.chk_soc_dict.clear()
        
        self.update_plots()
        self.log_msg("All session data cleared.", "blue")

    def closeEvent(self, event):
        self.handle_hard_disconnect("Application closing")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())