from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QSizePolicy, 
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox)
import constants

class HardwareLimitsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Hardware Limits")
        self.layout = QFormLayout(self)
        
        self.curr = QLineEdit(str(constants.MAX_CURRENT_MA))
        self.vmax = QLineEdit(str(constants.MAX_VOLTAGE_MV))
        self.fmin = QLineEdit(str(constants.MIN_FREQ_HZ))
        self.fmax = QLineEdit(str(constants.MAX_FREQ_HZ))
        self.inactivity = QLineEdit(str(constants.INACTIVITY_TIMEOUT_MS))
        self.ack = QLineEdit(str(constants.ACK_TIMEOUT_MS))
        
        self.layout.addRow("Max Current (mA):", self.curr)
        self.layout.addRow("Max Voltage (mV):", self.vmax)
        self.layout.addRow("Min Freq (Hz):", self.fmin)
        self.layout.addRow("Max Freq (Hz):", self.fmax)
        self.layout.addRow("Inactivity Timeout (ms):", self.inactivity)
        self.layout.addRow("ACK Timeout (ms):", self.ack)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def accept(self):
        try:
            if int(self.fmin.text()) > int(self.fmax.text()):
                QMessageBox.warning(self, "Invalid Input", "Minimum frequency cannot be greater than maximum frequency.")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers for all limits.")
            return
        super().accept()

class GraphSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graph Settings")
        self.layout = QFormLayout(self)
        
        self.datapoints = QLineEdit(str(constants.MAX_DATAPOINTS))
        self.update_ms = QLineEdit(str(constants.GRAPH_UPDATE_MS))
        
        self.layout.addRow("Data points in memory:", self.datapoints)
        self.layout.addRow("Graph Render Interval (ms):", self.update_ms)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def accept(self):
        try:
            int(self.datapoints.text())
            int(self.update_ms.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers.")
            return
        super().accept()

        
class CollapsibleGroupBox(QWidget):
    def __init__(self, title, v_policy=QSizePolicy.Policy.Maximum, stretch=0, parent=None):
        super().__init__(parent)
        self.default_v_policy = v_policy
        self.active_stretch = stretch  
        self.setSizePolicy(QSizePolicy.Policy.Preferred, self.default_v_policy)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 8) 
        main_layout.setSpacing(0)
        
        self.toggle_btn = QPushButton(f"▼ {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True) 
        self.toggle_btn.toggled.connect(self.on_toggle)
        
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        
        main_layout.addWidget(self.toggle_btn)
        main_layout.addWidget(self.content_area)
        self.title = title
        self.update_theme(False) 
        
    def update_theme(self, is_dark):
        if is_dark:
            self.toggle_btn.setStyleSheet("QPushButton { text-align: left; font-weight: bold; padding: 6px; border: 1px solid #555555; border-radius: 3px; background-color: #3b3b3b; color: white; } QPushButton:checked { background-color: #555555; }")
            self.content_area.setStyleSheet("QWidget#ContentArea { border: 1px solid #555555; border-top: none; border-bottom-left-radius: 3px; border-bottom-right-radius: 3px; }")
        else:
            self.toggle_btn.setStyleSheet("QPushButton { text-align: left; font-weight: bold; padding: 6px; border: 1px solid #a0a0a0; border-radius: 3px; background-color: #e8e8e8; color: black; } QPushButton:checked { background-color: #dcdcdc; }")
            self.content_area.setStyleSheet("QWidget#ContentArea { border: 1px solid #a0a0a0; border-top: none; border-bottom-left-radius: 3px; border-bottom-right-radius: 3px; }")
        
    def on_toggle(self, checked):
        self.content_area.setVisible(checked)
        self.toggle_btn.setText(f"{'▼' if checked else '▶'} {self.title}")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, self.default_v_policy if checked else QSizePolicy.Policy.Fixed)
        try:
            parent = self.parentWidget()
            if parent and parent.layout():
                parent.layout().setStretchFactor(self, self.active_stretch if checked else 0)
        except Exception: pass
            
    def setLayout(self, layout):
        layout.setContentsMargins(8, 8, 8, 8)
        self.content_area.setLayout(layout)