import sys
import shutil
import subprocess
import cups
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QMessageBox, QListWidget
)
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAE PS SAVER")
        self.setFixedSize(1000, 700)
        self.statusBar().showMessage("Ready")

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

        # Button layout
        button_layout = QHBoxLayout()

        self.button1 = QPushButton("Open PDF", self)
        self.button1.clicked.connect(self.open_pdf)
        button_layout.addWidget(self.button1)

        self.button2 = QPushButton("Save PDF", self)
        self.button2.clicked.connect(self.save_pdf)
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("Reset CUPS", self)
        self.button3.clicked.connect(self.button3_clicked)
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("Set Output Dir", self)
        self.button4.clicked.connect(self.button4_clicked)
        button_layout.addWidget(self.button4)

        self.refresh_jobs_button = QPushButton("Refresh Jobs", self)
        self.refresh_jobs_button.clicked.connect(self.load_print_jobs)
        button_layout.addWidget(self.refresh_jobs_button)

        main_layout.addLayout(button_layout)

        # PDF viewer
        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.pdf_viewer)

        # Job list widget
        self.job_list = QListWidget(self)
        main_layout.addWidget(self.job_list)

        self.current_pdf_path = None
        self.load_print_jobs()

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "/home/pi", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            self.current_pdf_path = file_path
            self.statusBar().showMessage("PDF loaded.")

    def save_pdf(self):
        if self.current_pdf_path:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf)")
            if save_path:
                shutil.copy(self.current_pdf_path, save_path)
                self.statusBar().showMessage(f"PDF saved to {save_path}")
                QMessageBox.information(self, "Saved", f"PDF saved to:\n{save_path}")
        else:
            self.statusBar().showMessage("No PDF to save.")
            QMessageBox.warning(self, "Warning", "No PDF file is currently opened.")

    def button3_clicked(self):
        try:
            subprocess.run(["sudo", "systemctl", "restart", "cups"], check=True)
            self.statusBar().showMessage("CUPS restarted successfully.")
            QMessageBox.information(self, "CUPS", "CUPS service restarted successfully.")
        except subprocess.CalledProcessError as e:
            self.statusBar().showMessage("Failed to restart CUPS.")
            QMessageBox.critical(self, "Error", f"Failed to restart CUPS:\n{e}")

    def button4_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Select PDF Output Directory")
        if folder:
            config_path = "/etc/cups/cups-pdf.conf"
            try:
                with open(config_path, 'r') as f:
                    lines = f.readlines()

                with open(config_path, 'w') as f:
                    for line in lines:
                        if line.strip().startswith("Out "):
                            f.write(f"Out {folder}\n")
                        else:
                            f.write(line)

                subprocess.run(["sudo", "systemctl", "restart", "cups"], check=True)
                self.statusBar().showMessage(f"PDF output directory set to {folder}")
                QMessageBox.information(self, "Directory Set", f"CUPS-PDF output set to:\n{folder}")
            except Exception as e:
                self.statusBar().showMessage("Failed to update output directory.")
                QMessageBox.critical(self, "Error", f"Could not update cups-pdf.conf:\n{e}")
        else:
            self.statusBar().showMessage("Directory selection canceled.")

    def load_print_jobs(self):
        try:
            conn = cups.Connection()
            jobs = conn.getJobs()
            self.job_list.clear()
            if not jobs:
                self.job_list.addItem("No active print jobs.")
            for job_id, job in jobs.items():
                state = job.get("job-state", 0)
                state_str = {
                    3: "Pending",
                    4: "Held",
                    5: "Processing",
                    6: "Stopped",
                    7: "Canceled",
                    8: "Aborted",
                    9: "Completed"
                }.get(state, "Unknown")
                self.job_list.addItem(f"Job {job_id}: {job['job-name']} - {state_str}")
            self.statusBar().showMessage("Job list updated.")
        except Exception as e:
            self.job_list.addItem("Error retrieving jobs.")
            self.statusBar().showMessage("Failed to retrieve CUPS job list.")
            QMessageBox.critical(self, "Error", f"Could not connect to CUPS:\n{e}")


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
