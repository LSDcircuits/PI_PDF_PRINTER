import sys 

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QScrollArea #for the inteface of the GUI
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAE PS SAVER") #Top name of the window
        self.setFixedSize(1000, 700) # width and height of the window
        
        #Widget layout 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # open the pdf with a button 
        #cups_setup
        #set geometry of buttons (x, y, width, height)
        self.button1 = QPushButton("button1", self)
        self.button1.setGeometry(50, 50, 100, 40) 
        self.button1.clicked.connect(self.open_pdf) # button is pressed and self.open_pdf is used to open the pdf
        


        self.button2 = QPushButton("button2", self)
        self.button2.setGeometry(300, 50, 100, 40) 
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton("button3", self)
        self.button3.setGeometry(550, 50, 100, 40) 
        self.button3.clicked.connect(self.button3_clicked)

        self.button4 = QPushButton("button4", self)
        self.button4.setGeometry(800, 50, 100, 40) 
        self.button4.clicked.connect(self.button4_clicked)

        #pdf viewer
        self.pdf_viewer = QPdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)

        #configure to load the full document
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomFactor(1.0)


        # add widget to layout
        layout.addWidget(self.pdf_viewer)

    def open_pdf(self):
        #opening the pdf file
        file_path, _ = QFileDialog.getOpenFileName(self,"Open PDF File", "/Users/ldaid/python_project/pdf_loc", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_document.load(file_path)

        print("button 1 clicked")

    def button2_clicked(self):
        print("button 2 clicked")

    def button3_clicked(self):
        print("button 3 clicked")

    def button4_clicked(self):
        print("button 4 clicked")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
