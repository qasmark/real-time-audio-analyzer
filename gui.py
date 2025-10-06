import sys
import sounddevice as sd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QFileDialog, QStatusBar)
from PyQt5.QtCore import pyqtSlot
import pyqtgraph as pg
import numpy as np
from analyzer import AudioAnalyzer


class AnalyzerGUI(QMainWindow):
    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer

        self.setWindowTitle("Анализатор звука")
        self.setGeometry(100, 100, 900, 700)

        self.history_size = 200
        self.amp_history = np.zeros(self.history_size)
        self.freq_history = np.zeros(self.history_size)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Устройство ввода:"))
        self.device_combo = QComboBox()
        self.populate_devices()
        device_layout.addWidget(self.device_combo)
        layout.addLayout(device_layout)

        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Старт")
        self.stop_btn = QPushButton("Стоп")
        self.clear_btn = QPushButton("Очистить")
        self.save_btn = QPushButton("Сохранить анализ")

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addWidget(self.save_btn)
        layout.addLayout(controls_layout)

        info_layout = QHBoxLayout()
        self.amp_label = QLabel("Амплитуда (RMS): 0.0000")
        self.freq_label = QLabel("Частота (Гц): 0.00")
        info_layout.addWidget(self.amp_label)
        info_layout.addWidget(self.freq_label)
        layout.addLayout(info_layout)

        self.amp_plot = pg.PlotWidget(title="Амплитуда")
        self.amp_plot.setYRange(0, 0.3)
        self.amp_line = self.amp_plot.plot(pen='y')

        self.freq_plot = pg.PlotWidget(title="Частота")
        self.freq_plot.setYRange(0, 2000)
        self.freq_line = self.freq_plot.plot(pen='c')

        layout.addWidget(self.amp_plot)
        layout.addWidget(self.freq_plot)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Готово к работе. Выберите устройство и нажмите 'Старт'.")

    def populate_devices(self):
        devices = self.analyzer.get_devices()
        for device in devices:
            self.device_combo.addItem(device['name'], userData=device['id'])

        try:
            default_device_id = sd.default.device[0]
            if default_device_id != -1:
                index = self.device_combo.findData(default_device_id)
                if index != -1:
                    self.device_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Не удалось определить устройство по умолчанию: {e}")

    def _connect_signals(self):
        self.start_btn.clicked.connect(self.start_analysis)
        self.stop_btn.clicked.connect(self.analyzer.stop)
        self.save_btn.clicked.connect(self.save_analysis)
        self.clear_btn.clicked.connect(self.clear_data_and_plots)

        self.analyzer.new_data.connect(self.update_plots)
        self.analyzer.status_changed.connect(self.statusBar().showMessage)

    def clear_data_and_plots(self):
        """Очищает историю в анализаторе и сбрасывает графики."""
        # 1. Говорим анализатору очистить свою внутреннюю историю
        self.analyzer.clear_history()

        # 2. Очищаем массивы, используемые для отрисовки
        self.amp_history.fill(0)
        self.freq_history.fill(0)

        # 3. Принудительно обновляем графики, чтобы они стали пустыми
        self.amp_line.setData(self.amp_history)
        self.freq_line.setData(self.freq_history)


    def start_analysis(self):
        selected_device_id = self.device_combo.currentData()
        self.analyzer.set_device(selected_device_id)
        self.analyzer.start()

    def save_analysis(self):
        self.analyzer.stop()

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить анализ", "", "CSV Files (*.csv)")
        if file_path:
            self.analyzer.save_history(file_path)

    @pyqtSlot(float, float)
    def update_plots(self, amp, freq):
        self.amp_label.setText(f"Амплитуда (RMS): {amp:.4f}")
        self.freq_label.setText(f"Частота (Гц): {freq:.2f}")

        self.amp_history = np.roll(self.amp_history, -1)
        self.amp_history[-1] = amp
        self.freq_history = np.roll(self.freq_history, -1)
        self.freq_history[-1] = freq

        self.amp_line.setData(self.amp_history)
        self.freq_line.setData(self.freq_history)

    def closeEvent(self, event):
        self.analyzer.stop()
        event.accept()