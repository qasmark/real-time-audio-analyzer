import sys
from PyQt5.QtWidgets import QApplication
from analyzer import AudioAnalyzer
from gui import AnalyzerGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    audio_analyzer = AudioAnalyzer()
    main_window = AnalyzerGUI(analyzer=audio_analyzer)

    main_window.show()
    sys.exit(app.exec_())