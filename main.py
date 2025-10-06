import sys
from PyQt5.QtWidgets import QApplication
from analyzer import AudioAnalyzer
from gui import AnalyzerGUI

# --- Конфигурация ---
# python -m sounddevice
# Указывается номер входного девайса
DEVICE_NAME = 11

if __name__ == "__main__":
    try:
        audio_analyzer = AudioAnalyzer(device_name=DEVICE_NAME)

        app = QApplication(sys.argv)
        main_window = AnalyzerGUI(analyzer=audio_analyzer)
        main_window.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import sounddevice as sd
        print("\nДоступные аудио-устройства:")
        print(sd.query_devices())