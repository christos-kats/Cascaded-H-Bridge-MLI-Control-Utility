import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class TelemetryGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(5, 2.5))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumHeight(100)
        self.ax = self.fig.add_subplot(111)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.canvas)

    def apply_theme(self, is_dark_mode):
        bg_color, fg_color, grid = ('#2b2b2b', 'white', '#555555') if is_dark_mode else ('#ffffff', 'black', 'black')
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor('#1e1e1e' if is_dark_mode else '#ffffff')
        self.ax.tick_params(colors=fg_color)
        self.ax.xaxis.label.set_color(fg_color)
        self.ax.yaxis.label.set_color(fg_color)
        self.ax.title.set_color(fg_color)
        for spine in self.ax.spines.values(): spine.set_edgecolor(grid)

    def export_png(self, path):
        self.fig.savefig(path)
        
    def draw_soc(self, session, chk_soc_dict, show_titles, show_legends, is_dark_mode):
        self.ax.clear()
        has_data = False
        if len(session.time_soc) > 0:
            for cell_id, data_points in session.soc_data.items():
                chk = chk_soc_dict.get(cell_id)
                if chk and chk.isChecked() and len(session.time_soc) == len(data_points):
                    self.ax.plot(session.time_soc, data_points, label=f"Module {cell_id}")
                    has_data = True
                    
            if has_data:
                if show_titles: self.ax.set_title("Battery Module States of Charge (SOC)")
                self.ax.set_ylabel("SOC (%)")
                if show_legends: self.ax.legend(loc="upper left")
                self.ax.grid(True)
                
        self.apply_theme(is_dark_mode)
        self.fig.tight_layout()
        self.canvas.draw()

    def draw_power(self, session, chk_voltage, chk_current, unit_mode, show_titles, show_legends, is_dark_mode):
        self.ax.clear()
        has_data = False
        mult = 1 if unit_mode == "mV/mA" else 1000.0
        
        if len(session.time_pwr) > 0:
            y_volts = [v / mult for v in session.voltage_data]
            y_currs = [c / mult for c in session.current_data]
            
            if chk_voltage.isChecked() and len(y_volts) == len(session.time_pwr):
                self.ax.plot(session.time_pwr, y_volts, 'b-', label="Voltage (mV)" if mult == 1 else "Voltage (V)")
                has_data = True
            if chk_current.isChecked() and len(y_currs) == len(session.time_pwr):
                self.ax.plot(session.time_pwr, y_currs, 'r-', label="Current (mA)" if mult == 1 else "Current (A)")
                has_data = True
                
            if has_data:
                if show_titles: self.ax.set_title("System Power Info")
                self.ax.set_xlabel("Time (s)")
                if show_legends: self.ax.legend(loc="upper left")
                self.ax.grid(True)
                
        self.apply_theme(is_dark_mode)
        self.fig.tight_layout()
        self.canvas.draw()