import sqlite3
import requests
import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QTableView, QLineEdit, QPushButton, QMessageBox,
                             QDialog, QFormLayout, QSpinBox, QLineEdit as QLE, QDialogButtonBox)
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel


def get_posts():
    r = requests.get('https://jsonplaceholder.typicode.com/posts')
    return r.json()


def insert_posts():
    for element in get_posts():
        cursor.execute(
            'INSERT OR REPLACE INTO posts (user_id,id,title,body) VALUES(?,?,?,?)',
            (element["userId"], element["id"], element["title"], element["body"])
        )


def insert_new_post(user_id, title, body):
    cursor.execute(
        'INSERT OR REPLACE INTO posts (user_id,id,title,body) VALUES(?,?,?,?)',
        (user_id, title, body)
    )


def delete_post(post_id):
    cursor.execute(
        'DELETE FROM posts WHERE id == (?)',
        (post_id,)
    )


def search_post_by_title(search_text):
    cursor.execute('f"SELECT id, user_id, title, body FROM your_table WHERE title LIKE ' % {search_text} % '"')
    posts = cursor.fetchall()


def view_all_posts():
    # Выбираем всех пользователей
    cursor.execute('SELECT * FROM posts')
    posts = cursor.fetchall()

    # Выводим результаты
    for post in posts:
        print(post)


def view_user_posts(userid):
    # Выбираем посты одного пользователя
    cursor.execute('SELECT * FROM posts WHERE user_id=?', (userid,))
    posts = cursor.fetchall()

    # Выводим результаты
    for post in posts:
        print(post)


# Создаем подключение к базе данных (файл my_database.db будет создан)
connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

# Создаем таблицу posts
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id integer,
title TEXT,
body TEXT 
)'''
               )

insert_posts()
# view_all_posts()
# view_user_posts(12)
# выравнивание ctrl+alt+L
# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()


########################################################


class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить запись")
        layout = QFormLayout()
        self.user_id_input = QSpinBox()
        self.title_input = QLE()
        self.body_input = QLE()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addRow("User ID:", self.user_id_input)
        layout.addRow("Title:", self.title_input)
        layout.addRow("Body:", self.body_input)
        layout.addRow("", self.buttonBox)
        self.setLayout(layout)


class UpdateRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать запись")
        layout = QFormLayout()
        self.post_id_input = QSpinBox()
        self.title_input = QLE()
        self.body_input = QLE()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addRow("Title:", self.title_input)
        layout.addRow("Body:", self.body_input)
        layout.addRow("", self.buttonBox)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("База данных")

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName('my_database.db')  # Замените на имя вашей БД
        # Код создания таблицы:
        query = QSqlQuery()
        query.exec("""
                        CREATE TABLE IF NOT EXISTS posts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            title TEXT,
                            body TEXT
                        )
                    """)

        if query.lastError().isValid():
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании таблицы: {query.lastError().text()}")
            sys.exit(1)
        if not self.db.open():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных")
            sys.exit(1)

        self.model = QSqlQueryModel()
        self.update_table()
        self.table_view = None

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по заголовку")
        self.search_bar.textChanged.connect(self.search)

        # self.refresh_button = QPushButton("Обновить")
        # self.refresh_button.clicked.connect(self.update_table)

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_record)

        self.update_button = QPushButton("Редактировать")
        self.update_button.clicked.connect(self.update_record)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_record)

        table_layout = QVBoxLayout()
        table_layout.addWidget(self.search_bar)
        # table_layout.addWidget(self.refresh_button)
        table_layout.addWidget(self.add_button)
        table_layout.addWidget(self.update_button)
        table_layout.addWidget(self.delete_button)
        table_layout.addWidget(QTableView())
        table_layout.addWidget(self.create_table_view())

        central_widget = QWidget()
        central_widget.setLayout(table_layout)
        self.setCentralWidget(central_widget)

    def create_table_view(self):
        view = QTableView()
        view.setModel(self.model)
        view.horizontalHeader().setStretchLastSection(True)
        self.table_view = view
        return view

    def update_table(self):
        query = QSqlQuery("SELECT id, user_id, title, body FROM posts")  # Замените your_table на имя вашей таблицы
        self.model.setQuery(query)

    def search(self, text):
        query = QSqlQuery(
            f"SELECT id, user_id, title, body FROM posts WHERE title LIKE '%{text}%'")
        self.model.setQuery(query)

    def add_record(self):
        dialog = AddRecordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_id = dialog.user_id_input.value()
            title = dialog.title_input.text()
            body = dialog.body_input.text()

            query = QSqlQuery()
            query.prepare(
                "INSERT INTO posts (user_id, title, body) VALUES (?, ?, ?)")
            query.addBindValue(user_id)
            query.addBindValue(title)
            query.addBindValue(body)
            if query.exec_():
                self.update_table()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить запись")

    def update_record(self):
        selection = self.table_view.currentIndex()
        id_to_update = selection.sibling(selection.row(), 0).data()
        if id_to_update == None:
            return

        user_id = selection.sibling(selection.row(), 1).data()
        title_to_update = selection.sibling(selection.row(), 2).data()
        body_to_update = selection.sibling(selection.row(), 3).data()

        dialog = UpdateRecordDialog(self)
        dialog.post_id_input.setValue(id_to_update)
        dialog.title_input.setText(title_to_update)
        dialog.body_input.setText(body_to_update)

        if dialog.exec_() == QDialog.Accepted:
            title = dialog.title_input.text()
            body = dialog.body_input.text()

            query = QSqlQuery()
            query.prepare("INSERT OR REPLACE INTO posts (id,user_id,title,body) VALUES(?,?,?,?)")
            query.addBindValue(id_to_update)
            query.addBindValue(user_id)
            query.addBindValue(title)
            query.addBindValue(body)
            if query.exec_():
                self.update_table()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось редактировать запись")

    def delete_record(self):
        selection = self.table_view.currentIndex()
        id_to_delete = selection.sibling(selection.row(), 0).data()
        if id_to_delete == None:
            return

        if QMessageBox.question(self, "Подтверждение", "Удалить запись?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            query = QSqlQuery()
            query.prepare("DELETE FROM posts WHERE id = ?")
            query.addBindValue(id_to_delete)
            if query.exec_():
                self.update_table()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить запись")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
