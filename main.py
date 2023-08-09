import os
import requests
from bs4 import BeautifulSoup
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, QLineEdit, QTableWidget,
                               QTextEdit, QDialog, QVBoxLayout, QLineEdit, QTableWidgetItem, QWidget, QFileDialog)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from requests.exceptions import RequestException

from Chain import Chain

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件，里面定义了 OPENAI_API_KEY

class DownloadButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.file_path = None

class ChatDialog(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chain Chat")

        self.layout = QVBoxLayout()

        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Enter your question...")
        self.input_field.returnPressed.connect(self.send_message)
        self.layout.addWidget(self.input_field)

        self.setLayout(self.layout)
        self.pdf_path = pdf_path  # 这里设置pdf_path属性
        self.chain = Chain(self.pdf_path)



    def send_message(self):
        user_message = self.input_field.text()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            response = self.get_response(user_message)  # 获取函数的响应
            self.chat_display.append(f"Bot: {response}")
            self.input_field.clear()

    def get_response(self, message):
        # 这里你可以调用你的指定函数来获取响应
        # 为了简化，我只是返回了一个简单的响应
        message = self.chain.get_answer(message)
        # return f"Received: {message}"
        return message

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("arXiv Paper Searcher")

        self.layout = QVBoxLayout()

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Enter search term...")
        self.layout.addWidget(self.search_field)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_arxiv)
        self.layout.addWidget(self.search_button)

        self.result_table = QTableWidget(0, 4)
        self.result_table.setHorizontalHeaderLabels(["Title", "Link", "Action","Chain"])
        self.layout.addWidget(self.result_table)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def clean_filename(self, filename):
        return ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in filename)

    def search_arxiv(self):
        search_term = self.search_field.text()
        try:
            response = requests.get(f'http://export.arxiv.org/api/query?search_query=all:{search_term}&start=0&max_results=10')
            response.raise_for_status()
        except RequestException as e:
            print(f"Error occurred during request: {e}")
            return

        try:
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            self.result_table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                title = entry.title.string
                file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
                link = entry.id.string.replace('abs', 'pdf') + ".pdf"
                self.result_table.setItem(i, 0, QTableWidgetItem(title))
                self.result_table.setItem(i, 1, QTableWidgetItem(link))

                cleaned_title = self.clean_filename(title)
                file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
                file_path = os.path.join(file_dir, f"{cleaned_title}.pdf")

                download_button = DownloadButton("Open" if os.path.exists(file_path) else "Download")
                download_button.file_path = file_path
                if os.path.exists(file_path):
                    download_button.clicked.connect(self.open_paper)
                    chain_button = QPushButton("Chain")
                    chain_button.clicked.connect(self.open_chain_dialog)
                    self.result_table.setCellWidget(i, 3, chain_button)  # 注意这里的索引变为3，因为我们添加了一个新的列
                else:
                    download_button.clicked.connect(self.download_paper)
                self.result_table.setCellWidget(i, 2, download_button)
                

        except Exception as e:
            print(f"Error occurred during parsing: {e}")

    def download_paper(self):
        button = self.sender()
        index = self.result_table.indexAt(button.pos())
        link = self.result_table.item(self.result_table.indexAt(button.pos()).row(), 1).text()
        try:
            response = requests.get(link, stream=True, allow_redirects=True)
            with open(button.file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            button.setText("Open")
            button.clicked.disconnect()
            button.clicked.connect(self.open_paper)

            chain_button = QPushButton("Chain")
            chain_button.clicked.connect(self.open_chain_dialog)
            self.result_table.setCellWidget(index.row(), 3, chain_button)  # 注意这里的索引变为3，因为我们添加了一个新的列

        except Exception as e:
            print(f"Error occurred during downloading: {e}")

    def open_paper(self):
        button = self.sender()
        QDesktopServices.openUrl(QUrl.fromLocalFile(button.file_path))
    
    def open_chain_dialog(self):
    # 获取PDF路径
        button = self.sender()
        index = self.result_table.indexAt(button.pos())
        pdf_path = self.result_table.cellWidget(index.row(), 2).file_path  # 假设第2列是"Action"列，其中存储了PDF路径

        dialog = ChatDialog(pdf_path, self)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
