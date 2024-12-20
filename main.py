import sys
import sqlite3
import requests  # Для работы с API
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QLineEdit, QPushButton, \
    QHBoxLayout, QInputDialog, QMessageBox
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5.QtCore import Qt
# QApplication: Основной класс для управления приложением.
# QMainWindow: Основное окно приложения.
# QTableView: Виджет для отображения табличных данных.
# QVBoxLayout, QHBoxLayout: Компоновщики для размещения виджетов.
# QLineEdit, QPushButton: Виджеты для ввода текста и кнопок.
# QInputDialog, QMessageBox: Диалоговые окна для ввода данных и отображения сообщений.
# QSqlDatabase, QSqlTableModel, QSqlQuery: Классы для работы с базой данных SQLite.
# Qt: Содержит константы, такие как Qt.Horizontal для работы с заголовками таблицы

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Приложение для работы с базой данных")
        self.setGeometry(100, 100, 1000, 600)

        # Основной виджет и компоновка
        self.central_widget = QWidget()#пустой виджет, который можно использовать как контейнер для других виджетов
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Поля фильтрации
        self.filter_layout = QHBoxLayout()

        self.filter_user_id = QLineEdit()
        self.filter_user_id.setPlaceholderText("Фильтр по ID пользователя")
        self.filter_layout.addWidget(self.filter_user_id)

        self.filter_title = QLineEdit()
        self.filter_title.setPlaceholderText("Фильтр по заголовку")
        self.filter_layout.addWidget(self.filter_title)

        self.filter_body = QLineEdit()
        self.filter_body.setPlaceholderText("Фильтр по тексту")
        self.filter_layout.addWidget(self.filter_body)

        self.filter_button = QPushButton("Применить фильтр")
        self.filter_button.clicked.connect(self.filter_data)
        self.filter_layout.addWidget(self.filter_button)

        self.layout.addLayout(self.filter_layout)

        # Виджет таблицы
        self.table_view = QTableView()
        self.layout.addWidget(self.table_view)

        # Кнопки
        self.update_button = QPushButton("Обновить")
        self.add_button = QPushButton("Добавить")
        self.delete_button = QPushButton("Удалить")
        self.import_button = QPushButton("Выгрузить данные из API")  # Новая кнопка

        # Кнопки по горизонтали
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.import_button)  # Добавляем новую кнопку
        self.layout.addLayout(button_layout)

        # Подключение к БД и настройка модели
        self.connect_to_db()
        self.setup_model()

        # Обработчики
        self.add_button.clicked.connect(self.add_record)
        self.delete_button.clicked.connect(self.delete_record)
        self.update_button.clicked.connect(self.update_data)
        self.import_button.clicked.connect(self.import_data_from_api)  # Обработчик кнопки

    def connect_to_db(self):
        self.db = QSqlDatabase.addDatabase("QSQLITE")#соединение с БД #Аргумент "QSQLITE" указывает на тип базы данных, с которой вы хотите работать
        self.db.setDatabaseName("database.db") #Этот метод задает имя файла базы данных для соединения

        if not self.db.open():
            print("Не удалось подключиться к базе данных.")
            sys.exit(1)

        # Создание таблицы, если она не существует
        query = QSqlQuery(self.db)
        query.exec_("""CREATE TABLE IF NOT EXISTS record (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        title TEXT,
                        body TEXT
                    )""")

    def setup_model(self):
        # Настройка модели для QTableView
        self.model = QSqlTableModel()#Это класс в PyQt, который представляет собой модель данных для работы с таблицами в базе данных
        self.model.setTable("record")
        self.model.select()#Этот метод выполняет SQL-запрос SELECT * FROM record для загрузки данных из таблицы record в модель

        # Отображение нужных столбцов
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "ID пользователя")
        self.model.setHeaderData(2, Qt.Horizontal, "Заголовок")
        self.model.setHeaderData(3, Qt.Horizontal, "Текст")

        # Связываем модель с таблицей
        self.table_view.setModel(self.model)

    def filter_data(self):
        # Создаем фильтры Создается пустой список filters, который будет содержать условия фильтрации
        filters = []
        #Извлекается текст из поля filter_user_id
        user_id = self.filter_user_id.text()
        if user_id:
            filters.append(f"user_id LIKE '%{user_id}%'")
        #Если текст не пустой, добавляется условие фильтрации в список filters. Условие ищет строки, где user_id содержит указанный текст.
        title = self.filter_title.text()
        if title:
            filters.append(f"title LIKE '%{title}%'")

        body = self.filter_body.text()
        if body:
            filters.append(f"body LIKE '%{body}%'")

        # Применяем фильтры к модели
        #Все условия фильтрации из списка filters объединяются в одну строку с помощью оператора AND.
        filter_query = " AND ".join(filters)
        self.model.setFilter(filter_query)#Фильтр применяется к модели данных с помощью метода setFilter()
        self.model.select()#Затем вызывается метод select(), чтобы обновить модель и отобразить отфильтрованные данные

    def add_record(self):
        user_id, ok1 = QInputDialog.getInt(self, "Ввод", "Введите ID пользователя:")
        if not ok1:
            return

        if user_id < 0:
            QMessageBox.warning(self, "Ошибка", "ID пользователя не может быть отрицательным!")
            return

        title, ok2 = QInputDialog.getText(self, "Ввод", "Введите заголовок:")
        if not ok2 or not title.strip():
            QMessageBox.warning(self, "Ошибка", "Заголовок не может быть пустым!")
            return

        body, ok3 = QInputDialog.getText(self, "Ввод", "Введите текст:")
        if not ok3 or not body.strip():
            QMessageBox.warning(self, "Ошибка", "Текст не может быть пустым!")
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO record (user_id, title, body) VALUES (?, ?, ?)")
        query.addBindValue(user_id)#Этот метод добавляет значение (user_id) в подготовленный SQL-запрос
        query.addBindValue(title)
        query.addBindValue(body)

        if query.exec_():
            self.model.select()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить запись.")

    def delete_record(self):
        index = self.table_view.selectionModel().currentIndex()
        #Эта строка кода получает индекс текущего выделенного элемента в таблице и сохраняет его в переменной index
        if not index.isValid():
            return

        record_id = self.model.data(self.model.index(index.row(), 0))
        #Эта строка кода извлекает данные из первого столбца (0) выделенной строки (index.row()) и сохраняет их в переменной record_id
        reply = QMessageBox.question(self, "Удалить", "Вы уверены, что хотите удалить эту запись?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            query = QSqlQuery(self.db)
            query.exec_(f"DELETE FROM record WHERE id = {record_id}")
            self.model.select()

    def update_data(self):
        self.model.select()

    def import_data_from_api(self):
        # Выгрузка данных из API
        try:
            response = requests.get("https://jsonplaceholder.typicode.com/posts")
            response.raise_for_status()
            posts = response.json()

            query = QSqlQuery(self.db)

            for post in posts:
                query.prepare("INSERT INTO record (user_id, title, body) VALUES (?, ?, ?)")
                query.addBindValue(post['userId'])
                query.addBindValue(post['title'])
                query.addBindValue(post['body'])
                query.exec_()

            self.model.select()
            QMessageBox.information(self, "Успех", "Данные успешно загружены из API!")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {e}")


# Запуск приложения
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
