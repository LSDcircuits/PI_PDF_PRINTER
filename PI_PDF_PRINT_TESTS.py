import sys
import shutil
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QLineEdit
)
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt, QThread, Signal
import os

CONFIG_FILE = "listener_config.txt"
RAWPRINT_SERVER_PATH = "/usr/local/bin/rawprint_server.sh"
RAWPRINT_SCRIPT_PATH = "/usr/local/bin/rawprint.sh"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = f.read().splitlines()
        ip = lines[0] if len(lines) > 0 else ""
        port = lines[1] if len(lines) > 1 else ""
        mask = lines[2] if len(lines) > 2 else "24"
        return ip, port, mask
    return "", "", "24"

def save_config(ip, port, mask):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"{ip}\n{port}\n{mask}\n")

# --- MODIFIED: Always create a new rawprint_server.sh with the new port
def write_rawprint_server(port):
    script = f"""#!/bin/bash

while true; do
  nc -l -p {port} | /usr/local/bin/rawprint.sh
done

"""
    try:
        # Remove old script if exists
        if os.path.exists(RAWPRINT_SERVER_PATH):
            os.remove(RAWPRINT_SERVER_PATH)
        # Write new one
        with open(RAWPRINT_SERVER_PATH, "w") as f:
            f.write(script)
        return True, f"rawprint_server.sh updated to port {port}."
    except Exception as e:
        return False, f"Failed to update rawprint_server.sh: {e}"

def make_scripts_executable():
    try:
        subprocess.run(["sudo", "chmod", "+x", RAWPRINT_SCRIPT_PATH], check=True)
        subprocess.run(["sudo", "chmod", "+x", RAWPRINT_SERVER_PATH], check=True)
        return True, "Scripts are now executable."
    except Exception as e:
        return False, f"Failed to make scripts executable: {e}"

class ListenerThread(QThread):
    job_received = Signal(str)
    error = Signal(str)

    def __init__(self, ip="", port=""):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self):
        try:
            subprocess.run(["sudo", "pkill", "-f", RAWPRINT_SERVER_PATH], check=False)
            env = os.environ.copy()
            if self.port:
                env["LISTEN_PORT"] = self.port
            process = subprocess.Popen(
                ["sudo", RAWPRINT_SERVER_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            for line in iter(process.stdout.readline, ""):
                if line.strip():
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        cae_label = QLabel("CAE", self)
        cae_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        cae_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(cae_label)

        welcome_label = QLabel("Welcome to PI_printer", self)
        welcome_label.setStyleSheet("font-size: 12px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_label)

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

        self.config_button = QPushButton("Set IP/Port/Mask", self)
        self.config_button.setStyleSheet("background-color: darkblue; color: white; border-radius: 5px; padding: 10px;")
        self.config_button.clicked.connect(self.show_config_inputs)
        button_layout.addWidget(self.config_button)

        main_layout.addLayout(button_layout)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.pdf_viewer)

        self.current_pdf_path = None

        # ----------- Config Input Widgets (hidden by default) -----------
        self.config_input_widget = QWidget()
        config_layout = QVBoxLayout()
        self.config_input_widget.setLayout(config_layout)
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.mask_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP address")
        self.port_input.setPlaceholderText("Enter port (e.g. 9100)")
        self.mask_input.setPlaceholderText("Enter subnet mask bits (e.g. 24)")

        config_layout.addWidget(QLabel("Set IP Address (also used as Gateway and DNS):"))
        config_layout.addWidget(self.ip_input)
        config_layout.addWidget(QLabel("Set Listener Port:"))
        config_layout.addWidget(self.port_input)
        config_layout.addWidget(QLabel("Set Subnet Mask Bits:"))
        config_layout.addWidget(self.mask_input)

        self.save_config_button = QPushButton("Save")
        self.save_config_button.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_config_button)
        self.config_input_widget.hide()
        main_layout.addWidget(self.config_input_widget)
        # ---------------------------------------------------------------

        ip, port, mask = load_config()
        self.ip_input.setText(ip)
        self.port_input.setText(port)
        self.mask_input.setText(mask)
        self.listener_ip = ip
        self.listener_port = port
        self.subnet_mask = mask

        self.update_status("Application started.")
        self.start_listener()

    def show_config_inputs(self):
        self.config_input_widget.setVisible(not self.config_input_widget.isVisible())

    def save_config(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        mask = self.mask_input.text().strip()
        if not ip or not port or not mask:
            self.update_status("IP, port, and subnet mask must not be empty.")
            return
        save_config(ip, port, mask)
        self.listener_ip = ip
        self.listener_port = port
        self.subnet_mask = mask

        ok, msg = write_rawprint_server(port)
        self.update_status(msg)
        ok2, msg2 = make_scripts_executable()
        self.update_status(msg2)
        self.set_static_ip(ip, mask)
        self.config_input_widget.hide()
        self.restart_listener()

    # --- MODIFIED: Use IP for address, gateway, and DNS
    def set_static_ip(self, ip, mask="24", interface="Wired connection 1"):
        gateway = ip
        dns = ip
        try:
            subprocess.run([
                "sudo", "nmcli", "con", "mod", interface,
                "ipv4.addresses", f"{ip}/{mask}",
                "ipv4.method", "manual"
            ], check=True)
            subprocess.run([
                "sudo", "nmcli", "con", "mod", interface,
                "ipv4.gateway", gateway
            ], check=True)
            subprocess.run([
                "sudo", "nmcli", "con", "mod", interface,
                "ipv4.dns", dns
            ], check=True)
            subprocess.run([
                "sudo", "nmcli", "con", "down", interface
            ], check=True)
            subprocess.run([
                "sudo", "nmcli", "con", "up", interface
            ], check=True)
            self.update_status(f"Static IP/gateway/dns set to {ip}/{mask} for {interface}")
        except subprocess.CalledProcessError as e:
            self.update_status(f"Failed to set static IP: {e}")

    def start_listener(self):
        self.listener_thread = ListenerThread(ip=self.listener_ip, port=self.listener_port)
        self.listener_thread.job_received.connect(self.update_status)
        self.listener_thread.error.connect(self.update_status)
        self.listener_thread.start()

    def restart_listener(self):
        if hasattr(self, "listener_thread") and self.listener_thread.isRunning():
            self.listener_thread.terminate()
            self.listener_thread.wait()
        self.start_listener()

    def system_reset(self):
        try:
            subprocess.run(["sudo", "systemctl", "stop", "cups"], check=True)
            self.update_status("CUPS service stopped.")
            subprocess.run(["sudo", "systemctl", "start", "cups"], check=True)
            self.update_status("CUPS service started.")
            subprocess.run(["sudo", "systemctl", "restart", "cups"], check=True)
            self.update_status("CUPS service restarted.")
        except subprocess.CalledProcessError as e:
            self.update_status(f"Error while resetting CUPS: {e}")

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "/var/spool/cups-pdf/ANONYMOUS", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            self.current_pdf_path = file_path
            self.update_status(f"PDF opened: {file_path}")
        else:
            self.update_status("No PDF file selected.")

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

    def clear_data(self):
        directory = "/var/spool/cups-pdf/ANONYMUS"
        try:
            if os.path.exists(directory):
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
        # --- MODIFIED: Show multiple messages if called twice in save_config
        prev = self.status_label.text()
        if prev and prev != message:
            self.status_label.setText(prev + "\n" + message)
        else:
            self.status_label.setText(message)

    def closeEvent(self, event):
        if hasattr(self, "listener_thread") and self.listener_thread.isRunning():
            self.listener_thread.terminate()
            self.listener_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
