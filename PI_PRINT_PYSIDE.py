import sys
import shutil
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt

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
        
        self.button1 = QPushButton("Start Listener", self)
        self.button1.setStyleSheet("background-color: black; color: white; border-radius: 5px; padding: 10px;")
        self.button1.clicked.connect(self.start_listener)
        button_layout.addWidget(self.button1)

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

    def start_listener(self):
        try:
            # Execute the rawprint_server.sh script
            subprocess.run(["sudo", "/usr/local/bin/rawprint_server.sh"], check=True)
            print("Listener started successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error while starting the listener: {e}")

    def system_reset(self):
        try:
            # Disable CUPS
            subprocess.run(["sudo", "systemctl", "stop", "cups"], check=True)
            print("CUPS service stopped.")

            # Enable CUPS
            subprocess.run(["sudo", "systemctl", "start", "cups"], check=True)
            print("CUPS service started.")

            # Restart CUPS
            subprocess.run(["sudo", "systemctl", "restart", "cups"], check=True)
            print("CUPS service restarted.")
        except subprocess.CalledProcessError as e:
            print(f"Error while resetting CUPS: {e}")

    def open_pdf(self):
        # Opening the pdf file
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "/Users/ldaid/python_project/pdf_loc", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            self.current_pdf_path = file_path
        print("Open PDF clicked")

    def save_pdf(self):
        if self.current_pdf_path:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf)")
            if save_path:
                shutil.copy(self.current_pdf_path, save_path)
                print(f"PDF saved to {save_path}")
        else:
            print("No PDF file is currently opened.")
        print("Save PDF To clicked")

    def clear_data(self):
        print("Clear Data clicked")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
