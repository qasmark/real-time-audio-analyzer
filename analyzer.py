import numpy as np
import sounddevice as sd
import queue
import threading
from scipy.fft import rfft, rfftfreq
from scipy.io import wavfile


class AudioAnalyzer:
    """
    Класс для захвата и анализа аудиосигнала в отдельном потоке.
    """
    def __init__(self, device_name, sample_rate=44100, buffer_size=2048):
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = 1

        self.audio_queue = queue.Queue()
        self.is_running = False
        self._thread = None
        self._stream = None

        self._lock = threading.Lock()
        self.latest_amplitude = 0.0
        self.latest_frequency = 0.0

    def _audio_callback(self, indata, frames, time, status):
        """Callback-функция для sounddevice. Вызывается в потоке аудио."""
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def _processing_loop(self):
        """Основной цикл обработки данных из очереди. Работает в self._thread."""
        while self.is_running:
            try:
                audio_data = self.audio_queue.get(timeout=1)

                audio_data = audio_data.flatten()
                amplitude = np.sqrt(np.mean(audio_data ** 2))

                windowed_data = audio_data * np.hanning(len(audio_data))
                yf = rfft(windowed_data)
                xf = rfftfreq(len(audio_data), 1 / self.sample_rate)
                idx = np.argmax(np.abs(yf[1:])) + 1
                frequency = xf[idx]

                with self._lock:
                    self.latest_amplitude = amplitude
                    self.latest_frequency = frequency

            except queue.Empty:
                continue

    def get_latest_results(self):
        """Возвращает последние вычисленные значения."""
        with self._lock:
            return self.latest_amplitude, self.latest_frequency

    def start(self):
        """Запускает захват и анализ звука."""
        if self.is_running:
            print("Анализатор уже запущен.")
            return

        print("Запуск анализатора...")
        self.is_running = True

        try:
            self._stream = sd.InputStream(
                device=self.device_name,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback,
                dtype='float32'
            )
            self._stream.start()
            self._thread = threading.Thread(target=self._processing_loop)
            self._thread.start()
            print("Анализатор успешно запущен.")
        except Exception as e:
            self.is_running = False
            print(f"Ошибка при запуске потока: {e}")
            raise

    def stop(self):
        """Останавливает захват и анализ."""
        if not self.is_running:
            return

        print("Остановка анализатора...")
        self.is_running = False

        if self._thread:
            self._thread.join()

        if self._stream:
            self._stream.stop()
            self._stream.close()

        # Очищаем очередь на случай, если там что-то осталось
        while not self.audio_queue.empty():
            self.audio_queue.get()

        print("Анализатор остановлен.")

    def process_file(self, file_path):
        """Обрабатывает WAV-файл, эмулируя поток."""
        if self.is_running:
            self.stop()  # Останавливаем живой поток перед обработкой файла
        try:
            samplerate, data = wavfile.read(file_path)
            if data.dtype != np.float32:
                data = data.astype(np.float32) / np.iinfo(data.dtype).max

            if data.ndim > 1:
                data = data[:, 0]

            self.sample_rate = samplerate
            print(f"Файл '{file_path}' загружен. Частота дискретизации: {samplerate} Гц.")

            self.is_running = True
            self._thread = threading.Thread(target=self._processing_loop)
            self._thread.start()

            for i in range(0, len(data), self.buffer_size):
                chunk = data[i:i + self.buffer_size]
                if len(chunk) < self.buffer_size:
                    chunk = np.pad(chunk, (0, self.buffer_size - len(chunk)))
                self.audio_queue.put(chunk)

            print("Обработка файла завершена. Нажмите 'Стоп' для сброса.")

        except Exception as e:
            print(f"Ошибка при обработке файла: {e}")