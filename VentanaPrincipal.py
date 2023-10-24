from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QSizePolicy
from novaventa import NovaVentaPage  # Asegúrate de que novaventa.py esté en el mismo directorio que este archivo
from yerbabuena import YerbaBuenaPage  # Asegúrate de que yerbabuena.py esté en el mismo directorio que este archivo
from loguin import LoguinPage  # Asegúrate de que loguin.py esté en el mismo directorio que este archivo
from PyQt5.QtGui import QIcon

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ventana Principal")
        self.setWindowIcon(QIcon('D:/auto_pedidos/icono.png'))
        self.setGeometry(100, 100, 300, 200)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        self.button_novaventa = QPushButton("NovaVenta")
        self.button_novaventa.clicked.connect(self.open_novaventa)
        self.button_novaventa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Hace que el botón se expanda para llenar el espacio disponible
        self.button_novaventa.setStyleSheet("font-size: 24px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.button_novaventa)

        self.button_yerbabuena = QPushButton("YerbaBuena")
        self.button_yerbabuena.clicked.connect(self.open_yerbabuena)
        self.button_yerbabuena.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Hace que el botón se expanda para llenar el espacio disponible
        self.button_yerbabuena.setStyleSheet("font-size: 24px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.button_yerbabuena)

        self.button_loguin = QPushButton("Loguin")
        self.button_loguin.clicked.connect(self.open_loguin)
        self.button_loguin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Hace que el botón se expanda para llenar el espacio disponible
        self.button_loguin.setStyleSheet("font-size: 24px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.button_loguin)

        self.novaventa_page = None
        self.yerbabuena_page = None
        self.loguin_page = None

    def show_main_buttons(self):
        self.button_novaventa.show()
        self.button_yerbabuena.show()
        self.button_loguin.show()

    def open_novaventa(self):
        if self.novaventa_page is None:
            self.novaventa_page = NovaVentaPage(self.show_main_buttons)
            self.layout.addWidget(self.novaventa_page)
        self.novaventa_page.show()
        self.button_novaventa.hide()
        self.button_yerbabuena.hide()
        self.button_loguin.hide()

    def open_yerbabuena(self):
        if self.yerbabuena_page is None:
            self.yerbabuena_page = YerbaBuenaPage(self.show_main_buttons)
            self.layout.addWidget(self.yerbabuena_page)
        self.yerbabuena_page.show()
        self.button_novaventa.hide()
        self.button_yerbabuena.hide()
        self.button_loguin.hide()

    def open_loguin(self):
        if self.loguin_page is None:
            self.loguin_page = LoguinPage(self.show_main_buttons)
            self.layout.addWidget(self.loguin_page)
        self.loguin_page.show()
        self.button_novaventa.hide()
        self.button_yerbabuena.hide()
        self.button_loguin.hide()

app = QApplication([])
window = VentanaPrincipal()
window.show()
app.exec_()
