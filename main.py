import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from models.project import ProjectConfig
from ui.main_window import MainWindow


def main():
    config = ProjectConfig()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("个人工作台")

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
