import sys
import shutil
import subprocess
import tempfile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QLineEdit
)
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
import os

# I WILL DOCUMENT HOW THIS CODE WORKS HERE AND Reference to this file as a source
# here i define define memory
# firsly the listener_conf file contain 3 variables, kept in a different file so config doesent change when restarting.
# file contains // in those lines. the file is only made once using sudo nano and saved, any other changes are made in this software. 
# 1 ip
# 2 port
# 3 mask

# this file is accessed using the os library
CONFIG_FILE = "listener_config.txt"
RAWPRINT_SERVER_PATH = "/usr/local/bin/rawprint_server.sh"
RAWPRINT_SCRIPT_PATH = "/usr/local/bin/rawprint.sh"
# rawprint_server.sh and rawprint.sh are shell files i noted the info in the file below:
# --------------------------( rawprint_server.sh )---------------------------------
# 1 !/bin/bash
# 2 
# 3  while true; do
# 4  nc -l -p 9100 | /usr/local/bin/rawprint.sh
# 5  done
# --------------------------------------------------------------------------
# here i use os and shutil to write and 

# here the config is set up using os to get acess to the CONFIG_FILE and define these variables,
# it first checks if the file exist and acess the info enen if nothing is there it returns nothing mask is always set to 32 unless specified hence the else "" 
# since most printers use a 32 bit mask on it. 
# s.read().plitlines() is a func of os which allows to read and split line on a .txt file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = f.read().splitlines()
        ip = lines[0] if len(lines) > 0 else ""
        port = lines[1] if len(lines) > 1 else ""
        mask = lines[2] if len(lines) > 2 else "32"
        return ip, port, mask
    return "", "", "32"

# here uses os to link the written variables on the GUI to save to the text file.
# f.write() to write the config to the file. 
def save_config(ip, port, mask):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"{ip}\n{port}\n{mask}\n")
# to write to the rawprint server its good to know what it does.
# rawprint server is a shell script for using the nc linux tool in this the port is defined, the ip in the rawprint.sh 
def write_rawprint_server(port):
    script = f"""#!/bin/bash

while true; do
  nc -l -p {port} | /usr/local/bin/rawprint.sh
done

"""
    try:
        # Write to a temp file first
        with tempfile.NamedTemporaryFile("w", delete=False) as tmpfile:
            tmpfile.write(script)
            tmp_filename = tmpfile.name
        # Move with sudo using subprocess which is a tool used on python to make command line executions. 
        subprocess.run(["sudo", "mv", tmp_filename, RAWPRINT_SERVER_PATH], check=True)
        return True, f"rawprint_server.sh updated to port {port}."
    except Exception as e:
        return False, f"Failed to update rawprint_server.sh: {e}"
# here i make it executable using subprocess which writes chmod on the terminal to the shell script path
def make_scripts_executable():
    try:
        subprocess.run(["sudo", "chmod", "+x", RAWPRINT_SCRIPT_PATH], check=True)
        subprocess.run(["sudo", "chmod", "+x", RAWPRINT_SERVER_PATH], check=True)
        return True, "Scripts are now executable."
    except Exception as e:
        return False, f"Failed to make scripts executable: {e}"
        
# this function i used to kill the process, this is useful since the listener should stop when changes are made.
# this fucntion uses also Subprocress to run terminal commands
def stop_nc_listener():
    try:
        # Kill any running nc (netcat) processes related to the server script
        subprocess.run(["sudo", "pkill", "-f", RAWPRINT_SERVER_PATH], check=False)
        subprocess.run(["sudo", "pkill", "-f", "nc -l -p"], check=False)  # Extra: kill leftover nc
        return True, "Stopped running listeners."
    except Exception as e:
        return False, f"Failed to stop listeners: {e}"


class ListenerThread(QThread):
    job_received = Signal(str)
    error = Signal(str)

    def __init__(self, ip="", port=""):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self):
        try:
            stop_nc_listener()  # Always stop before starting new listener
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


#-------------------------------------------------(GUI RELATED SECTIONS)------------------------------------------------------------
# here for the GUI it defined as a main window so the app it self, its related to making the buttons and linking to the different fucntions
# more details on how it can be set up set up on the QT documentation https://doc.qt.io/qtforpython-6/modules.html
# if youre more curious about how its set up in detail you can search the fucntion there
# its useful to go through the documentation to undertand this code since it has many premade icons for specific purposes to ease development QT
# i find it rather handy since it works just as documented.
# generally each button is defined and once defined, like on line 168 'cae_label = QLabel("CAE", self)' is defined and afer the "."
# its attributed to a function of QT in such ""cae_label.setStyleSheet("font-size: 48px; font-weight: bold;")"
# this is done for every button. 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # here is where the title, window size are set
        self.setWindowTitle("CAE PS SAVER")
        self.setFixedSize(1024, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # ---------- Top Right Off and Close Buttons ----------- 
        # for the off button i used a preset from the library QIcon.fromTheme("system-shutdown")
        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch()
        self.off_button = QPushButton()
        self.off_button.setIcon(QIcon.fromTheme("system-shutdown"))  # Uses system icon if available
        self.off_button.setFixedSize( 20, 20)
        self.off_button.setStyleSheet("background-color: transparent; border-radius: 12px;")
        self.off_button.setToolTip("Shut Down")
        self.off_button.clicked.connect(self.shutdown_system)
        top_btn_layout.addWidget(self.off_button)
        self.close_button = QPushButton("✖")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("background-color: transparent; border-radius: 12px; font-size: 12px; color: white;")
        self.close_button.setToolTip("Close Program")
        self.close_button.clicked.connect(self.close)
        top_btn_layout.addWidget(self.close_button)
        main_layout.addLayout(top_btn_layout)
        # ------------------------------------------------------
        # here the label at the top of the app is set as a graphic image using using QLabel
        cae_label = QLabel("CAE", self)
        cae_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        cae_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(cae_label)

        welcome_label = QLabel("Welcome to PI_printer", self)
        welcome_label.setStyleSheet("font-size: 12px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_label)

        # for buttons the QHboxLayout is used
        button_layout = QHBoxLayout()
        # & for each box in self (window) is referenced to another funtion 
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

        # this one specifically is for the status which would usuallt be printed in the terminal, useful for to see the logs 
        # like when nc sends a job to cups
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # here the button for opening a file is set and uses QPdf to display it
        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.pdf_viewer)

        self.current_pdf_path = None

        #  Config Input Widgets (hidden by default)
        # this widget opens when for chanig the IP, mask & port
        self.config_input_widget = QWidget()
        config_layout = QVBoxLayout()
        self.config_input_widget.setLayout(config_layout)
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.mask_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP address")
        self.port_input.setPlaceholderText("Enter port (e.g. 9100)")
        self.mask_input.setPlaceholderText("Enter subnet mask bits (e.g. 24)")

        # here is where the actual boxes are set up for the IP change
        config_layout.addWidget(QLabel("Set IP Address (also used as Gateway and DNS):"))
        config_layout.addWidget(self.ip_input)
        config_layout.addWidget(QLabel("Set Listener Port:"))
        config_layout.addWidget(self.port_input)
        config_layout.addWidget(QLabel("Set Subnet Mask Bits:"))
        config_layout.addWidget(self.mask_input)

        # IP change is linked to the load config fucntion which is executed with the save button
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

    def shutdown_system(self):
        self.update_status("Shutting down...")
        try:
            subprocess.Popen(["sudo", "shutdown", "now"])
        except Exception as e:
            self.update_status(f"Error shutting down: {e}")

    def show_config_inputs(self):
        self.config_input_widget.setVisible(not self.config_input_widget.isVisible())
        # so the save config file takes varables from self. (window) here is where its sent from self to the tmp file
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

        # the first function stop_nc_listener is important for this part since it needs to be stopped to be modified and executed 
        # with chmod
        ok_stop, msg_stop = stop_nc_listener()
        self.update_status(msg_stop)

        ok, msg = write_rawprint_server(port)
        self.update_status(msg)
        ok2, msg2 = make_scripts_executable()
        self.update_status(msg2)
        self.set_static_ip(ip, mask)
        self.config_input_widget.hide()
        self.restart_listener()

    # ----------------------------(here i mark a end to the graphical interfece and continue to functions linked to the buttons)----------------
    # ---------------------------------------------------( setting a static IP for the PC using subprocess)-------------------------------------
        # this part isnt very elegant, generally on linux you can make a file to set static values for network connections.
        # on debian for Pi, RAPSBIAN it just didnt work like im used to on normal debian or on arch so i used a method found on 
        # stack overflow which does it directly on to the temrinal, so i used Subprocess for this also, which works fine just adds alot code
        # IP is defined previously as seen and here is where its executed, the first functions did it in the listener class
    
    def set_static_ip(self, ip, mask="32", interface="Wired connection 1"):
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

    #here the listener thread from the class is stated, or configured to the window
    def start_listener(self):
        self.listener_thread = ListenerThread(ip=self.listener_ip, port=self.listener_port)
        self.listener_thread.job_received.connect(self.update_status)
        self.listener_thread.error.connect(self.update_status)
        self.listener_thread.start()
    # here its restarted and ran
    def restart_listener(self):
        if hasattr(self, "listener_thread") and self.listener_thread.isRunning():
            self.listener_thread.terminate()
            self.listener_thread.wait()
        self.start_listener()
        
    # this function is linked to the system reset button 
    # uses sub process to enter commands into the terminal
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
    # this function is used to open the pdf
    # this uses a func from the Qt lib to open the pdf and can speciy where in the file manager its open
    # by deafoult cups saves in thid file caled "ANONYMOUS" i open it there to ease the use of the user
    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "/var/spool/cups-pdf/ANONYMOUS", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)
            self.current_pdf_path = file_path
            self.update_status(f"PDF opened: {file_path}")
        else:
            self.update_status("No PDF file selected.")
            
    # this fucntion is used to save the pdf
    # using shutil and Qfiledialog i can save this pdf to a specific directory, i made the driver display in a 
    # directory i made called media so its more like in normal computers where external storage devices are locared in the media directory
    def save_pdf(self):
        if self.current_pdf_path:
            # Let user choose a directory, defaulting to /media (where USBs are usually mounted)
            directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save PDF", "/media")
            if directory:
                # Ask for a file name
                filename, _ = QFileDialog.getSaveFileName(self, "Save PDF As", os.path.join(directory, "output.pdf"), "PDF Files (*.pdf)")
                if filename:
                    shutil.copy(self.current_pdf_path, filename)
                    self.update_status(f"PDF saved to {filename}")
                else:
                    self.update_status("Save operation canceled.")
            else:
                self.update_status("No directory selected.")
        else:
            self.update_status("No PDF file is currently opened.")
    # here  i use os to remove files in a directory
    # rather handy and dint use subprocess with rm because i wanted to try something else. 
    def clear_data(self):
        directory = "/var/spool/cups-pdf/ANONYMOUS"
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
    # this is the fucntion which you see is called everywhere, its used to just display the status which would
    # normally be presented on the temrinal. 
    def update_status(self, message):
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
