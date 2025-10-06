import numpy as np
import sounddevice as sd
import queue
import threading
import time
import csv
from PyQt5.QtCore import QObject, pyqtSignal
from scipy.fft import rfft, rfftfreq
from collections import deque


class AudioAnalyzer(QObject):
    status_changed = pyqtSignal(str)
    new_data = pyqtSignal(float, float)

    def __init__(self, sample_rate=44100, buffer_size=2048):
        super().__init__()
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = 1
        self.device_id = None

        self.audio_queue = queue.Queue()
        self.is_running = False
        self._thread = None
        self._stream = None

        # 2. Заменяем list на deque с максимальной длиной
        # Рассчитаем примерный размер на 5 минут записи
        # (44100 / 2048) -> ~21.5 раз в секунду
        # 22 * 60 * 5 -> 6600
        # Возьмем с запасом, например, 100000 записей
        self.history = deque(maxlen=100000)

        self.start_time = 0

    def set_device(self, device_id):
        self.device_id = device_id
        print(f"Выбрано устройство: {device_id}")

    def _audio_callback(self, indata, frames, time, status):
        if status:
            self.status_changed.emit(f"Ошибка потока: {status}")
        self.audio_queue.put(indata.copy())

    def _processing_loop(self):
        while self.is_running:
            try:
                audio_data = self.audio_queue.get(timeout=1)
                audio_data = audio_data.flatten()

                amplitude = np.sqrt(np.mean(audio_data ** 2))

                windowed_data = audio_data * np.hanning(len(audio_data))
                yf = rfft(windowed_data)
                xf = rfftfreq(len(audio_data), 1 / self.sample_rate)
                idx = np.argmax(np.abs(yf[1:])) + 1
                frequency = xf[idx] if amplitude > 0.0001 else 0.0

                timestamp = time.time() - self.start_time
                self.history.append((timestamp, amplitude, frequency))
                self.new_data.emit(amplitude, frequency)

            except queue.Empty:
                continue

    def start(self):
        if self.is_running:
            self.status_changed.emit("Анализатор уже запущен.")
            return

        if self.device_id is None:
            self.status_changed.emit("Ошибка: Аудио-устройство не выбрано!")
            return

        self.is_running = True
        self.history.clear()
        self.start_time = time.time()

        try:
            self._stream = sd.InputStream(
                device=self.device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback,
                dtype='float32'
            )
            self._stream.start()
            self._thread = threading.Thread(target=self._processing_loop)
            self._thread.start()
            self.status_changed.emit(f"Анализ запущен на устройстве ID {self.device_id}")
        except Exception as e:
            self.is_running = False
            self.status_changed.emit(f"Ошибка запуска: {e}")

    def stop(self):
        if not self.is_running:
            return

        self.status_changed.emit("Остановка анализатора...")
        self.is_running = False

        if self._thread:
            self._thread.join()

        if self._stream:
            self._stream.stop()
            self._stream.close()

        while not self.audio_queue.empty():
            self.audio_queue.get()

        self.status_changed.emit("Остановлено.")

    def save_history(self, file_path):
        if not self.history:
            self.status_changed.emit("Нет данных для сохранения.")
            return

        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp_sec', 'amplitude_rms', 'frequency_hz'])
                # 3. deque можно записывать точно так же, как и list
                writer.writerows(self.history)
            self.status_changed.emit(f"Анализ сохранен в {file_path}")
        except Exception as e:
            self.status_changed.emit(f"Ошибка сохранения файла: {e}")

    def clear_history(self):
        self.history.clear()
        self.status_changed.emit("История и графики очищены.")

    @staticmethod
    def get_devices():
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({'id': i, 'name': device['name']})
        return input_devices