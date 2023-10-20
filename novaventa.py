from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QLabel, QTableWidget, QTableWidgetItem, QDialog, QGridLayout, QInputDialog, QMessageBox
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import sqlite3
import pandas as pd
from PyQt5.QtGui import QFont
import logging
from PyQt5.QtWidgets import QProgressBar  # Agregar importaciones

# Conéctate a la base de datos (o créala si no existe)
conn = sqlite3.connect('novaventa.db')

# Crea un cursor
c = conn.cursor()

# Crea la tabla de productos (si no existe)
c.execute('''
    CREATE TABLE IF NOT EXISTS products(
        name TEXT,
        catalog_price REAL,
        product_price REAL,
        code TEXT PRIMARY KEY
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS session_products(
        name TEXT,
        catalog_price REAL,
        product_price REAL,
        code TEXT PRIMARY KEY
    )
''')

# Guarda los cambios
conn.commit()

class NovaVenta:
    def __init__(self):
        # Configura el logging
        logging.basicConfig(filename='app.log', level=logging.INFO)
        
        # Inicia el navegador
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

        # Solicitar información de inicio de sesión al usuario
        self.username = input("Ingrese su nombre de usuario: ")
        self.password = input("Ingrese su contraseña: ")

        # Iniciar sesión
        self.login()

    def login(self):
        self.driver.get("https://comercio.novaventa.com.co/nautilusb2bstorefront/nautilus/es/COP/login")
        
        # Espera hasta que los campos de usuario y contraseña estén presentes
        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "j_username")))
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "j_password")))
        except NoSuchElementException:
            logging.error("No se encontraron los campos de inicio de sesión.")
            return
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        password_field.send_keys(Keys.RETURN)
    
    def retry(self, function, attempts=3, delay=2):
        for i in range(attempts):
            try:
                return function()
            except:
                if i < attempts - 1:  # Si no es el último intento
                    time.sleep(delay)
                else:
                    raise

    def get_current_cart_quantity(self):
        try:
            # Obtiene el texto que muestra la cantidad actual en el carrito
            cart_quantity_text = self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[@class='nav-items-total']"))).text
            return int(cart_quantity_text)
        except Exception as e:
            logging.error(f"Error al obtener la cantidad del carrito: {e}")
            return 0  # Retorna 0 como valor predeterminado en caso de error


    def process_orders(self, product_codes):
        conn = None
        try:
            # Conéctate a la base de datos
            conn = sqlite3.connect('novaventa.db')
            # Crea un cursor
            c = conn.cursor()
            
            # Elimina registros anteriores de session_products
            c.execute('DELETE FROM session_products')
            
            # Procesa cada código de producto
            for product_code in product_codes:
                    
                # Comprueba si el product_code tiene un guion "-"
                if '-' in product_code:
                    code, quantity = product_code.split('-')
                else:
                    code = product_code
                    quantity = 1  # Asume cantidad 1 si no se especifica una cantidad

                # Navega a la página del producto
                self.driver.get(f"https://comercio.novaventa.com.co/nautilusb2bstorefront/nautilus/es/COP/search/?text={code}")

                # Espera a que la página del producto cargue completamente
                self.wait.until(EC.visibility_of_element_located((By.XPATH, f"//div[starts-with(@data-product-code, '{code}_')]")))
            
                # Obtiene la cantidad inicial en el carrito antes de agregar el producto
                initial_quantity = self.get_current_cart_quantity()

                for _ in range(int(quantity)):
                    try:
                        # Selecciona el elemento div que contiene el producto
                        product_div = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//div[starts-with(@data-product-code, '{code}_')]")))
                    except:
                        print(f"Error: El producto con el código {code} no existe.")
                        continue
                    # Usando la función de reintento
                    self.retry(lambda: self.wait.until(EC.visibility_of_element_located((By.XPATH, f"//div[starts-with(@data-product-code, '{code}_')]"))))

                    # Recupera los atributos del producto
                    product_name = product_div.get_attribute('data-product-name')
                    product_catalog_price = product_div.get_attribute('data-product-catalog-price')
                    product_price = product_div.get_attribute('data-product-price')
                    product_code = product_div.get_attribute('data-product-code').split('_')[0]  # Solo queremos la parte del código antes del "-"

                    # Encuentra el botón dentro del div y haz clic en él
                    add_to_cart_button = product_div.find_element(By.XPATH, ".//button[text()='Agregar a mi pedido']")

                    c.execute('SELECT * FROM products WHERE code = ?', (product_code,))
                    if c.fetchone() is None:
                        # Si el producto no existe en products, inserta en ambas tablas
                        c.execute('INSERT INTO products (name, catalog_price, product_price, code) VALUES (?, ?, ?, ?)', (product_name, product_catalog_price, product_price, product_code))
                        c.execute('INSERT INTO session_products (name, catalog_price, product_price, code) VALUES (?, ?, ?, ?)', (product_name, product_catalog_price, product_price, product_code))                    
                    else:
                        # Si el producto ya existe, actualiza su información solo en products
                        c.execute('UPDATE products SET name = ?, catalog_price = ?, product_price = ? WHERE code = ?', (product_name, product_catalog_price, product_price, product_code))


                    self.driver.execute_script("arguments[0].click();", add_to_cart_button)

                    # Espera un poco para que la página tenga tiempo de procesar el clic
                    time.sleep(3)
                        
                # Obtiene la cantidad final en el carrito después de agregar el producto
                final_quantity = self.get_current_cart_quantity()

                # Verifica si la cantidad en el carrito se ha actualizado correctamente
                expected_quantity = initial_quantity + int(quantity)
                if final_quantity != expected_quantity:
                    logging.warning(f"Error: Se esperaba {expected_quantity} artículo(s) en el carrito, pero hay {final_quantity}.")
                         # Guarda los cambios
            conn.commit()

        except sqlite3.Error as e:
            logging.error(f"Error de SQLite: {e}")
        except Exception as e:
            logging.error(f"Error desconocido: {e}")
        finally:
            # Cierra la conexión a la base de datos si está abierta
            if conn:
                conn.close()
    
class NovaVentaPage(QWidget):
    def __init__(self, show_main_buttons):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Ingrese los códigos de los productos:")
        self.label.setFont(QFont(None, 12))  # Ajusta el tamaño de la fuente aquí
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont(None, 12))  # Ajusta el tamaño de la fuente aquí
        self.layout.addWidget(self.text_edit)

        self.button = QPushButton("Procesar pedidos")
        self.button.clicked.connect(self.process_orders)
        self.button.setStyleSheet("font-size: 24px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.button)

        self.button_show_products = QPushButton("Productos")
        self.button_show_products.clicked.connect(self.toggle_products_window)
        self.button_show_products.setStyleSheet("font-size: 25px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.button_show_products)
        # Crea la ventana de productos, pero no la muestra todavía
        self.products_window = ProductsWindow()
        
        self.text_edit_products = QTextEdit()
        self.text_edit_products.setReadOnly(True)  # Hace que el QTextEdit sea de solo lectura
        self.layout.addWidget(self.text_edit_products)
        self.text_edit_products.hide()  # Oculta el QTextEdit al inicio


        self.back_button = QPushButton("Atrás")
        self.back_button.clicked.connect(self.hide_and_show_main_buttons)
        self.back_button.setStyleSheet("font-size: 24px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.back_button)

        self.show_main_buttons = show_main_buttons
        self.novaventa = NovaVenta()  # Inicializa la instancia de NovaVenta
        # Añade una bandera para rastrear si la tabla está visible
        self.table_visible = False
        
        # Añadir una barra de progreso y una etiqueta para mostrar el estado
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Estado: Esperando...")
        self.layout.addWidget(self.status_label)

    def toggle_products_window(self):
        if self.products_window.isVisible():
            self.products_window.hide()
        else:
            self.products_window.show()

    def hide_and_show_main_buttons(self):
        self.hide()
        self.show_main_buttons()

    def process_orders(self):
        product_codes = [code.strip() for code in self.text_edit.toPlainText().split('\n') if code.strip()]
        if not product_codes:
            self.show_error("No hay códigos de productos para procesar.")
            return
        total_products = len(product_codes)
        self.progress_bar.setMaximum(total_products)  # Establecer el valor máximo de la barra de progreso

        for index, product_code in enumerate(product_codes):
            try:
                # Actualizar la barra de progreso y el mensaje de estado
                self.progress_bar.setValue(index + 1)
                self.status_label.setText(f"Estado: Procesando {product_code}...")
                self.novaventa.process_orders([product_code])  # Aquí asumo que tu función puede manejar un solo código de producto a la vez. Ajusta esto según sea necesario.
            except Exception as e:
                self.status_label.setText(f"Estado: Error al procesar {product_code}")
                self.show_error(str(e))

        self.status_label.setText("Estado: Completado")

    def show_error(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("Error")
        error_dialog.setInformativeText(message)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()
    
class ProductsWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.layout.addWidget(self.table, 0, 0, 1, 2)  # Añade la tabla al layout

        self.export_button = QPushButton("Exportar a Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setStyleSheet("font-size: 25px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.export_button, 1, 0)

        self.toggle_button = QPushButton("Mostrar productos de la sesión")
        self.toggle_button.clicked.connect(self.toggle_table)
        self.toggle_button.setStyleSheet("font-size: 25px")  # Ajusta el tamaño de la fuente del botón
        self.layout.addWidget(self.toggle_button, 1, 1)

        self.update_table()

    def toggle_table(self):
        if self.toggle_button.text() == "Mostrar productos de la sesión":
            self.update_table(session_only=True)
            self.toggle_button.setText("Mostrar todos los productos")
        else:
            self.update_table(session_only=False)
            self.toggle_button.setText("Mostrar productos de la sesión")

    def update_table(self, session_only=False):
        # Conéctate a la base de datos
        conn = sqlite3.connect('novaventa.db')

        # Crea un cursor
        c = conn.cursor()

        # Ejecuta una consulta
        if session_only:
            c.execute("SELECT * FROM session_products")
        else:
            c.execute("SELECT * FROM products")

        # Recoge los resultados
        rows = c.fetchall()

        # Cierra la conexión
        conn.close()

        # Configura el QTableWidget
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Código", "Precio Revista", "Precio Catálogo"])

        font = QFont()
        font.setPointSize(12)  # Ajusta el tamaño de la fuente aquí

        # Rellena la tabla
        for i, row in enumerate(rows):
            name_item = QTableWidgetItem(row[0])  # Nombre
            name_item.setFont(font)
            self.table.setItem(i, 0, name_item)

            code_item = QTableWidgetItem(row[3])  # Código
            code_item.setFont(font)
            self.table.setItem(i, 1, code_item)

            price_revista_item = QTableWidgetItem("${:,}".format(int(row[2])))  # Precio Revista
            price_revista_item.setFont(font)
            self.table.setItem(i, 2, price_revista_item)

            price_catalogo_item = QTableWidgetItem("${:,}".format(int(row[1])))  # Precio Catálogo
            price_catalogo_item.setFont(font)
            self.table.setItem(i, 3, price_catalogo_item)
    
    def export_to_excel(self):
        options = ["Todos los productos", "Productos de la sesión"]
        item, ok = QInputDialog.getItem(self, "Seleccionar opción", "Exportar:", options, 0, False)
        if ok and item:
            if item == options[0]:
                self._export_data_to_excel("SELECT * FROM products")
            else:
                self._export_data_to_excel("SELECT * FROM session_products")

    def _export_data_to_excel(self, query):
        # Conéctate a la base de datos
        conn = sqlite3.connect('novaventa.db')
        # Crea un cursor
        c = conn.cursor()
        # Ejecuta una consulta
        c.execute(query)
        # Recoge los resultados
        rows = c.fetchall()
        # Cierra la conexión
        conn.close()
        # Crea un DataFrame con los datos
        df = pd.DataFrame(rows, columns=["Nombre", "Precio Catálogo", "Precio Revista", "Código"])
        # Exporta los datos a un archivo de Excel
        df.to_excel("productos.xlsx", index=False)
