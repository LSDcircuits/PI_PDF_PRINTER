import sys
import shutil
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt, QThread, Signal
import os


class ListenerThread(QThread):
    job_received = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            # Stop any running instance of rawprint_server.sh
            subprocess.run(["sudo", "pkill", "-f", "/usr/local/bin/rawprint_server.sh"], check=False)  # Non-blocking stop

            # Start the rawprint_server.sh script and capture its output
            process = subprocess.Popen(
                ["sudo", "/usr/local/bin/rawprint_server.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Read the output line by line
            for line in iter(process.stdout.readline, ""):
                if line.strip():  # If the line is not empty
                    self.job_received.emit(f"Job received: {line.strip()}")

            process.stdout.close()
            process.wait()
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAE PS SAVER")
        self.setFixedSize(1000, 700)
        
        # Widget layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # CAE message
        cae_label = QLabel("CAE", self)
        cae_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        cae_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(cae_label)

        # Welcome message
        welcome_label = QLabel("Welcome to PI_printer", self)
        welcome_label.setStyleSheet("font-size: 12px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_label)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()

        self.button2 = QPushButton("SYSTEM Reset", self)
        self.button2.setStyleSheet("background-color: black; color: white; border-radius: 5px; padding: 10px;")
        self.button2.clicked.connect(self.system_reset)
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("Open PDF", self)
        self.button3.setStyleSheet("background-color: black; color: white; border-radius: 5px; padding: 10px;")
        self.button3.clicked.connect(self.open_pdf)
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("Save PDF To", self)
        self.button4.setStyleSheet("background-color: black; color: white; border-radius: 5px; padding: 10px;")
        self.button4.clicked.connect(self.save_pdf)
        button_layout.addWidget(self.button4)

        self.clear_data_button = QPushButton("Clear Data", self)
        self.clear_data_button.setStyleSheet("background-color: black; color: white; border-radius: 5px; padding: 10px;")
        self.clear_data_button.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_data_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # PDF viewer
        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)

        # Configure to load the full document
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)

        # Make the PDF viewer expand to fill the remaining space
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add pdf viewer to layout
        main_layout.addWidget(self.pdf_viewer)

        # Variable to store the path of the opened PDF
        self.current_pdf_path = None

        # Show startup message
        self.update_status("Application started.")

        # Start the listener thread
        self.start_listener()

    def start_listener(self):
        self.listener_thread = ListenerThread()
        self.listener_thread.job_received.connect(self.update_status)
        self.listener_thread.error.connect(self.update_status)
        self.listener_thread.start()

    def system_reset(self):
        try:
            # Disable CUPS
            subprocess.run(["sudo", "systemctl", "stop", "cups"], check=True)
            self.update_status("CUPS service stopped.")

            # Enable CUPS
            subprocess.run(["sudo", "systemctl", "start", "cups"], check=True)
            self.update_status("CUPS service started.")

            # Restart CUPS
            subprocess.run(["sudo", "systemctl", "restart", "cups"], check=True)
            self.update_status("CUPS service restarted.")
        except subprocess.CalledProcessError as e:
            self.update_status(f"Error while resetting CUPS: {e}")

    def open_pdf(self):
        # Opening the pdf file
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "/var/spool/cups-pdf/ANONYMOUS", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            self.current_pdf_path = file_path
            self.update_status(f"PDF opened: {file_path}")
        else:
            self.update_status("No PDF file selected.")
        print("Open PDF clicked")

    def save_pdf(self):
        if self.current_pdf_path:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf)")
            if save_path:
                shutil.copy(self.current_pdf_path, save_path)
                self.update_status(f"PDF saved to {save_path}")
            else:
                self.update_status("Save operation canceled.")
        else:
            self.update_status("No PDF file is currently opened.")
        print("Save PDF To clicked")

    def clear_data(self):
        directory = "/var/spool/cups-pdf/ANONYMUS"
        try:
            # Check if the directory exists
            if os.path.exists(directory):
                # Loop through and remove all files in the directory
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                self.update_status("All files in the directory have been deleted.")
            else:
                self.update_status("Directory does not exist.")
        except Exception as e:
            self.update_status(f"Error while clearing data: {e}")

    def update_status(self, message):
        self.status_label.setText(message)

    def closeEvent(self, event):
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.terminate()  # Forcefully stop the thread
        event.accept()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
