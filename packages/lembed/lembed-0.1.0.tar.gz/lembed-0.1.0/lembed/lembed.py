import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

class BrowserWindow(QMainWindow):
    def __init__(self, url):
        super().__init__()
        self.setWindowTitle("LEmbed Browser - PyQt6")
        self.resize(1200, 800)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.load(QUrl(url))

class LEmbed:
    def display(self, url):
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        window = BrowserWindow(url)
        window.show()

        # Run app.exec() only if this is the main QApplication
        # Prevents issues if QApplication already exists
        if not QApplication.instance():
            sys.exit(app.exec())
        else:
            app.exec()

# Singleton instance for easy use
lembed_instance = LEmbed()

def display(url):
    lembed_instance.display(url)
