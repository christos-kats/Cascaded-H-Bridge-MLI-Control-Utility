from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QRadioButton, 
                             QGridLayout, QComboBox, QTableWidget, QHeaderView, 
                             QCheckBox, QSizePolicy)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt
from widgets import CollapsibleGroupBox
from graphs import TelemetryGraph
import constants

class Ui_MainWindow:
    def setup_ui(self, window, settings):
        self.collapsible_boxes = []
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ==========================================
        # LEFT PANEL
        # ==========================================
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Connection
        conn_group = CollapsibleGroupBox("Connection", QSizePolicy.Policy.Maximum, stretch=0)
        self.collapsible_boxes.append(conn_group)
        conn_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(30)
        self.btn_connect = QPushButton("Connect")
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo, stretch=1)
        conn_layout.addWidget(self.btn_refresh)
        conn_layout.addWidget(self.btn_connect)
        conn_group.setLayout(conn_layout)
        left_panel_layout.addWidget(conn_group)

        # 2. Control
        control_group = CollapsibleGroupBox("Output Mode", QSizePolicy.Policy.Maximum, stretch=0)
        self.collapsible_boxes.append(control_group)
        control_layout = QGridLayout()
        self.radio_off = QRadioButton("OFF")
        self.radio_off.setChecked(True)
        self.radio_charging = QRadioButton("Charging Mode")
        self.lbl_current = QLabel("   Current:")
        self.input_current = QLineEdit("0")
        self.radio_dc = QRadioButton("DC Mode")
        self.lbl_voltage = QLabel("   Voltage:")
        self.input_voltage = QLineEdit("0")
        self.radio_ac = QRadioButton("AC Mode")
        self.lbl_amp = QLabel("   Amplitude:")
        self.input_amp = QLineEdit("0")
        self.lbl_freq = QLabel("   Frequency:")
        self.input_freq = QLineEdit(str(constants.MIN_FREQ_HZ))
        self.btn_send = QPushButton("Send Command")
        self.btn_send.setEnabled(False)
        self.btn_send.setMinimumHeight(40)

        control_layout.addWidget(self.radio_off, 0, 0, 1, 2)
        control_layout.addWidget(self.radio_charging, 1, 0, 1, 2)
        control_layout.addWidget(self.lbl_current, 2, 0)
        control_layout.addWidget(self.input_current, 2, 1)
        control_layout.addWidget(self.radio_dc, 3, 0, 1, 2)
        control_layout.addWidget(self.lbl_voltage, 4, 0)
        control_layout.addWidget(self.input_voltage, 4, 1)
        control_layout.addWidget(self.radio_ac, 5, 0, 1, 2)
        control_layout.addWidget(self.lbl_amp, 6, 0)
        control_layout.addWidget(self.input_amp, 6, 1)
        control_layout.addWidget(self.lbl_freq, 7, 0)
        control_layout.addWidget(self.input_freq, 7, 1)
        control_layout.setRowMinimumHeight(8, 15)
        control_layout.addWidget(self.btn_send, 9, 0, 1, 2)
        control_group.setLayout(control_layout)
        left_panel_layout.addWidget(control_group)

        # 3. Output Monitor (Uniform Layouts)
        monitor_group = CollapsibleGroupBox("Output Monitor", QSizePolicy.Policy.Maximum, stretch=0)
        self.collapsible_boxes.append(monitor_group)
        monitor_layout = QHBoxLayout()
        monitor_layout.setContentsMargins(15, 10, 15, 10)
        monitor_layout.setSpacing(15)
        
        def create_monitor_panel(title_text, default_val):
            panel_layout = QVBoxLayout()
            panel_layout.setSpacing(4)
            
            title_lbl = QLabel(title_text)
            title_lbl.setObjectName("MonitorTitle")
            title_font = QFont()
            title_font.setPointSize(8)
            title_font.setBold(True)
            title_lbl.setFont(title_font)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            val_lbl = QLabel(default_val)
            val_lbl.setObjectName("MonitorValue")
            val_lbl.setMinimumHeight(42)
            val_font = QFont()
            val_font.setPointSize(16)
            val_font.setBold(True)
            val_lbl.setFont(val_font)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            panel_layout.addWidget(title_lbl)
            panel_layout.addWidget(val_lbl)
            return panel_layout, val_lbl

        mode_layout, self.lbl_mon_mode = create_monitor_panel("MODE", "-")
        volt_layout, self.lbl_mon_volt = create_monitor_panel("VOLTAGE", "0 mV")
        curr_layout, self.lbl_mon_curr = create_monitor_panel("CURRENT", "0 mA")
        
        monitor_layout.addLayout(mode_layout, stretch=1)
        monitor_layout.addLayout(volt_layout, stretch=1)
        monitor_layout.addLayout(curr_layout, stretch=1)
        
        monitor_group.setLayout(monitor_layout)
        left_panel_layout.addWidget(monitor_group)

        # 4. Telemetry Table
        telemetry_group = CollapsibleGroupBox("Battery Module Information", QSizePolicy.Policy.Expanding, stretch=10)
        self.collapsible_boxes.append(telemetry_group)
        telemetry_layout = QVBoxLayout()
        self.cell_table = QTableWidget(0, 4)
        self.cell_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cell_table.verticalHeader().setVisible(False)
        self.cell_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        telemetry_layout.addWidget(self.cell_table)
        telemetry_group.setLayout(telemetry_layout)
        left_panel_layout.addWidget(telemetry_group, stretch=10)

        # 5. Config Table
        config_group = CollapsibleGroupBox("Battery Module Configurations", QSizePolicy.Policy.Expanding, stretch=10)
        self.collapsible_boxes.append(config_group)
        config_layout = QVBoxLayout()
        self.config_table = QTableWidget(0, 3)
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.config_table.verticalHeader().setVisible(False)
        self.config_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        config_layout.addWidget(self.config_table)
        config_group.setLayout(config_layout)
        left_panel_layout.addWidget(config_group, stretch=10)
        
        left_panel_layout.addStretch(0)
        left_panel_container = QWidget()
        left_panel_container.setLayout(left_panel_layout)
        left_panel_container.setFixedWidth(460)
        main_layout.addWidget(left_panel_container)

        # ==========================================
        # RIGHT PANEL
        # ==========================================
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # SOC Graph
        soc_group = CollapsibleGroupBox("Live SOC Data", QSizePolicy.Policy.Expanding, stretch=10)
        self.collapsible_boxes.append(soc_group)
        soc_layout = QVBoxLayout()
        self.soc_graph = TelemetryGraph()
        soc_layout.addWidget(self.soc_graph)
        
        # Checkbox Area
        soc_controls = QHBoxLayout()
        soc_controls.addWidget(QLabel("<b>Show SOC:</b>"))
        self.soc_chk_container = QHBoxLayout()
        soc_controls.addLayout(self.soc_chk_container)
        self.chk_soc_dict = {}
        
        soc_controls.addStretch()
        self.btn_exp_soc_csv = QPushButton("Export CSV")
        self.btn_exp_soc_png = QPushButton("Export PNG")
        soc_controls.addWidget(self.btn_exp_soc_csv)
        soc_controls.addWidget(self.btn_exp_soc_png)
        soc_layout.addLayout(soc_controls)
        soc_group.setLayout(soc_layout)
        right_panel_layout.addWidget(soc_group, stretch=10)

        # Power Graph
        pwr_group = CollapsibleGroupBox("Live Power Data", QSizePolicy.Policy.Expanding, stretch=10)
        self.collapsible_boxes.append(pwr_group)
        pwr_layout = QVBoxLayout()
        self.pwr_graph = TelemetryGraph()
        pwr_layout.addWidget(self.pwr_graph)
        pwr_controls = QHBoxLayout()
        pwr_controls.addWidget(QLabel("<b>Show Power:</b>"))
        self.chk_voltage = QCheckBox("Voltage")
        self.chk_current = QCheckBox("Current")
        self.chk_voltage.setChecked(True)
        self.chk_current.setChecked(True)
        pwr_controls.addWidget(self.chk_voltage)
        pwr_controls.addWidget(self.chk_current)
        pwr_controls.addStretch()
        self.btn_exp_pwr_csv = QPushButton("Export CSV")
        self.btn_exp_pwr_png = QPushButton("Export PNG")
        pwr_controls.addWidget(self.btn_exp_pwr_csv)
        pwr_controls.addWidget(self.btn_exp_pwr_png)
        pwr_layout.addLayout(pwr_controls)
        pwr_group.setLayout(pwr_layout)
        right_panel_layout.addWidget(pwr_group, stretch=10)

        # Console
        console_group = CollapsibleGroupBox("Info Console", QSizePolicy.Policy.Expanding, stretch=6)
        self.collapsible_boxes.append(console_group)
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        console_btns = QHBoxLayout()
        self.btn_clear_console = QPushButton("Clear Console")
        self.chk_auto_scroll = QCheckBox("Auto-Scroll to Bottom")
        self.chk_auto_scroll.setChecked(True)
        console_btns.addWidget(self.btn_clear_console)
        console_btns.addStretch()
        console_btns.addWidget(self.chk_auto_scroll)
        console_layout.addLayout(console_btns)
        console_group.setLayout(console_layout)
        right_panel_layout.addWidget(console_group, stretch=6)

        right_panel_container = QWidget()
        right_panel_container.setLayout(right_panel_layout)
        main_layout.addWidget(right_panel_container)

    def setup_menu(self, window, settings):
        menu_bar = window.menuBar()
        
        file_menu = menu_bar.addMenu("File")
        self.action_export_all = QAction("Export All Data to CSV", window)
        self.action_save_log = QAction("Save Console Log", window)
        self.action_exit = QAction("Exit", window)
        file_menu.addActions([self.action_export_all, self.action_save_log])
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        settings_menu = menu_bar.addMenu("Settings")
        self.action_hw_limits = QAction("Hardware Settings", window)
        self.action_baud = QAction("Connection Settings", window)
        self.action_graph_hist = QAction("Graph Settings", window)
        
        settings_menu.addActions([self.action_hw_limits, self.action_baud, self.action_graph_hist])

        view_menu = menu_bar.addMenu("View")
        self.action_expand_all = QAction("Expand All Panels", window)
        self.action_collapse_all = QAction("Collapse All Panels", window)
        view_menu.addActions([self.action_expand_all, self.action_collapse_all])
        view_menu.addSeparator()

        self.action_toggle_units = QAction("Display as Volts / Amps (V / A)", window, checkable=True)
        self.action_toggle_units.setChecked(settings.get("unit_mode") == "V/A")

        self.action_show_titles = QAction("Show Graph Titles", window, checkable=True)
        self.action_show_titles.setChecked(settings.get("show_titles"))
        
        self.action_show_legends = QAction("Show Graph Legends", window, checkable=True)
        self.action_show_legends.setChecked(settings.get("show_legends"))
        

        view_menu.addActions([self.action_toggle_units, self.action_show_titles, self.action_show_legends])
        view_menu.addSeparator()

        self.action_show_timestamps = QAction("Show Timestamps in Console", window, checkable=True)
        self.action_show_timestamps.setChecked(settings.get("show_timestamps"))
        self.action_show_raw = QAction("Show Raw Data in Console", window, checkable=True)
        self.action_show_raw.setChecked(settings.get("show_raw_telemetry", True))
        
        view_menu.addActions([self.action_show_timestamps, self.action_show_raw])
        view_menu.addSeparator()

        self.action_dark_mode = QAction("Dark Mode", window, checkable=True)
        self.action_dark_mode.setChecked(settings.get("is_dark_mode"))
        self.action_clear_data = QAction("Clear All Data", window)
        view_menu.addActions([self.action_dark_mode, self.action_clear_data])

        help_menu = menu_bar.addMenu("Help")
        self.action_protocol = QAction("Protocol Details", window)
        self.action_about = QAction("About", window)
        help_menu.addActions([self.action_protocol, self.action_about])