import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton,
    QFileDialog, QWidget, QVBoxLayout, QMessageBox
)
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAE PS SAVER")
        self.setFixedSize(900, 600)  # More Pi-friendly resolution

        # Start CUPS service on app launch
        self.ensure_cups_running()

        # Set up layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Buttons
        self.button1 = QPushButton("Open PDF", self)
        self.button1.setGeometry(50, 50, 100, 40)
        self.button1.clicked.connect(self.open_pdf)

        self.button2 = QPushButton("Check CUPS", self)
        self.button2.setGeometry(200, 50, 100, 40)
        self.button2.clicked.connect(self.check_cups_status)

        self.button3 = QPushButton("Open Last Print", self)
        self.button3.setGeometry(350, 50, 150, 40)
        self.button3.clicked.connect(self.load_last_pdf)

        self.button4 = QPushButton("Quit", self)
        self.button4.setGeometry(550, 50, 100, 40)
        self.button4.clicked.connect(self.close)

        # PDF Viewer
        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)

        layout.addWidget(self.pdf_viewer)

    def ensure_cups_running(self):
        try:
            subprocess.run(["sudo", "systemctl", "start", "cups"], check=True)
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to start CUPS service.")

    def check_cups_status(self):
        result = subprocess.run(["systemctl", "is-active", "cups"], capture_output=True, text=True)
        if "active" in result.stdout:
            QMessageBox.information(self, "CUPS Status", "CUPS is running.")
        else:
            QMessageBox.warning(self, "CUPS Status", "CUPS is NOT running.")

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", os.path.expanduser("~/PDF"), "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            print("PDF Loaded:", file_path)

    def load_last_pdf(self):
        pdf_dir = os.path.expanduser("~/PDF")
        try:
            files = sorted(
                (os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")),
                key=os.path.getmtime,
                reverse=True
            )
            if files:
                self.pdf_document.load(files[0])
                print("Loaded most recent PDF:", files[0])
            else:
                QMessageBox.information(self, "Info", "No PDFs found in ~/PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load recent PDF:\n{e}")


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()

