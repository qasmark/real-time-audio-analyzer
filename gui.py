import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QFileDialog
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import numpy as np
from analyzer import AudioAnalyzer


class AnalyzerGUI(QMainWindow):
    """
    Класс для графического интерфейса анализатора.
    """

    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer

        self.setWindowTitle("Анализатор звука в реальном времени")
        self.setGeometry(100, 100, 800, 600)

        # --- Данные для графиков ---
        self.history_size = 200  # Сколько точек хранить на графике
        self.amp_history = np.zeros(self.history_size)
        self.freq_history = np.zeros(self.history_size)

        self._init_ui()

        # --- Таймер для обновления GUI ---
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Старт (с микрофона)")
        self.stop_btn = QPushButton("Стоп")
        self.load_btn = QPushButton("Загрузить WAV файл")

        self.start_btn.clicked.connect(self.start_analysis)
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.load_btn.clicked.connect(self.load_file)

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.load_btn)
        layout.addLayout(controls_layout)

        # --- Панель информации ---
        info_layout = QHBoxLayout()
        self.amp_label = QLabel("Амплитуда (RMS): 0.0000")
        self.freq_label = QLabel("Частота (Гц): 0.00")
        info_layout.addWidget(self.amp_label)
        info_layout.addWidget(self.freq_label)
        layout.addLayout(info_layout)

        # --- Графики ---
        self.amp_plot = pg.PlotWidget(title="Амплитуда")
        self.amp_plot.setYRange(0, 0.3)
        self.amp_line = self.amp_plot.plot(pen='y')

        self.freq_plot = pg.PlotWidget(title="Частота")
        self.freq_plot.setYRange(0, 1500)
        self.freq_line = self.freq_plot.plot(pen='c')

        layout.addWidget(self.amp_plot)
        layout.addWidget(self.freq_plot)

    def update_plots(self):
        """Обновляет графики и текстовые поля."""
        amp, freq = self.analyzer.get_latest_results()

        self.amp_label.setText(f"Амплитуда (RMS): {amp:.4f}")
        self.freq_label.setText(f"Частота (Гц): {freq:.2f}")

        # Сдвигаем историю и добавляем новые значения
        self.amp_history = np.roll(self.amp_history, -1)
        self.amp_history[-1] = amp
        self.freq_history = np.roll(self.freq_history, -1)
        self.freq_history[-1] = freq if amp > 0.001 else 0  # Не показывать частоту в тишине

        self.amp_line.setData(self.amp_history)
        self.freq_line.setData(self.freq_history)

    def start_analysis(self):
        try:
            self.analyzer.start()
        except Exception as e:
            print(f"Не удалось запустить анализ: {e}")

    def stop_analysis(self):
        self.analyzer.stop()
        self.amp_history.fill(0)
        self.freq_history.fill(0)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать WAV файл", "", "WAV Files (*.wav)")
        if file_path:
            # Запускаем обработку файла в потоке анализатора
            self.analyzer.process_file(file_path)

    def closeEvent(self, event):
        self.stop_analysis()
        event.accept()