# src/widgets/reports_chart.py
from __future__ import annotations
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


MATPLOTLIB_AVAILABLE = False


def _matplotlib_disabled_by_env() -> bool:
    return os.environ.get("LOGIX_DISABLE_CHARTS", "0").strip() in {"1", "true", "True", "yes", "on"}


class ReportsChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = None
        self.canvas = None

        if _matplotlib_disabled_by_env():
            self._create_fallback_widget(layout)
            return

        global MATPLOTLIB_AVAILABLE
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
            from matplotlib.figure import Figure  # type: ignore
            import matplotlib.pyplot as plt  # type: ignore
            self._FigureCanvas = FigureCanvas
            self._Figure = Figure
            self._plt = plt
            MATPLOTLIB_AVAILABLE = True
        except Exception as e:
            print(f"Matplotlib not available or failed to initialize: {e}")
            MATPLOTLIB_AVAILABLE = False
            self._FigureCanvas = None
            self._Figure = None
            self._plt = None

        if MATPLOTLIB_AVAILABLE and self._Figure and self._FigureCanvas:
            try:
                self.figure = self._Figure(figsize=(12, 8))
                self.canvas = self._FigureCanvas(self.figure)
                layout.addWidget(self.canvas)
                self.load_static_demo_data()
            except Exception as e:
                print(f"Chart widget creation failed: {e}")
                self.figure = None
                self.canvas = None
                self._create_fallback_widget(layout)
        else:
            self._create_fallback_widget(layout)

    def _create_fallback_widget(self, layout):
        lbl = QLabel("📊 Charts require matplotlib\nInstall with: pip install matplotlib")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#6b7280; font-size: 14px; padding: 40px; background: white; border-radius: 8px;")
        layout.addWidget(lbl)

    def load_static_demo_data(self):
        try:
            if not MATPLOTLIB_AVAILABLE or not self.canvas or not self.figure:
                return
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            departments = ['IT', 'HR', 'Finance', 'Operations']
            present = [25, 15, 20, 30]
            late = [5, 3, 4, 8]
            absent = [2, 4, 1, 3]
            x = list(range(len(departments)))
            width = 0.25
            x_present = [i - width for i in x]
            x_late = x
            x_absent = [i + width for i in x]
            ax.bar(x_present, present, width=width, color="#10b981", label="Present", alpha=0.9)
            ax.bar(x_late, late, width=width, color="#f59e0b", label="Late", alpha=0.9)
            ax.bar(x_absent, absent, width=width, color="#ef4444", label="Absent", alpha=0.9)
            ax.set_xticks(x)
            ax.set_xticklabels(departments)
            ax.set_title('Sample Attendance Report', fontweight='bold')
            ax.set_ylabel('Number of Employees')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            ax.legend()
            self.figure.subplots_adjust(left=0.1, bottom=0.15, right=0.9, top=0.9)
            self.canvas.draw()
        except Exception as e:
            print(f"Failed to load demo chart data: {e}")

    def plot(self, labels: list[str], present: list[int], late: list[int], absent: list[int], title: str):
        try:
            if not MATPLOTLIB_AVAILABLE or not self.canvas or not self.figure:
                return
            n = min(len(labels), len(present), len(late), len(absent))
            labels = labels[:n]
            present = [int(p or 0) for p in present[:n]]
            late = [int(l or 0) for l in late[:n]]
            absent = [int(a or 0) for a in absent[:n]]
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            x = list(range(len(labels)))
            width = 0.25 if len(labels) > 0 else 0.25
            x_present = [i - width for i in x]
            x_late = x
            x_absent = [i + width for i in x]
            ax.bar(x_present, present, width=width, color="#10b981", label="Present", alpha=0.9)
            ax.bar(x_late, late, width=width, color="#f59e0b", label="Late", alpha=0.9)
            ax.bar(x_absent, absent, width=width, color="#ef4444", label="Absent", alpha=0.9)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=0 if len(labels) <= 6 else 20, ha='right')
            ax.set_title(title, fontweight='bold')
            ax.set_ylabel('Number of Employees')
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            ax.legend()
            self.figure.subplots_adjust(left=0.1, bottom=0.2 if len(labels) > 6 else 0.15, right=0.95, top=0.9)
            self.canvas.draw()
        except Exception as e:
            print(f"Chart plotting failed: {e}")

    def closeEvent(self, event):
        try:
            if getattr(self, '_plt', None) is not None and getattr(self, 'figure', None) is not None:
                self._plt.close(self.figure)
        except Exception as e:
            print(f"Error closing ReportsChartWidget: {e}")
        super().closeEvent(event)
# Widgets package for reusable UI components

