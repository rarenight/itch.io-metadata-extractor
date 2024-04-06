import sys
import os
import re
import requests
import json
import pyperclip
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QMessageBox, QLineEdit

class ItchioDownloaderV2(QWidget):

    auth_header = "" # Enter your API Key here

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Itch.io Downloader')
        self.setGeometry(100, 100, 300, 150)

        self.url_label = QLabel('Enter the Itch.io download URL (if Web GUI) or page URL (if Butler):')
        self.url_input = QLineEdit()

        self.extract_button_free = QPushButton('Extract Itch.io metadata (free)')
        self.extract_button_free.clicked.connect(self.extract_ids_free)

        self.extract_button_paid = QPushButton('Extract Itch.io metadata (paid)')
        self.extract_button_paid.clicked.connect(self.extract_ids_paid)

        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.extract_button_free)
        layout.addWidget(self.extract_button_paid)

        self.setLayout(layout)

    def extract_game_id_from_data_json(self, url):
        response = requests.get(url + "/data.json")
        if response.status_code == 200:
            data = response.json()
            return data.get("id")
        else:
            return None
    

    def extract_ids_free(self):
        url = self.url_input.text()
        version_id = None
        if "w3g3a5v6.ssl.hwcdn.net" in url:
            match = re.search(r'game/(\d+)/(\d+)', url)
            if match:
                game_id, version_id = match.groups()
        else:
            game_id = self.extract_game_id_from_data_json(url)

        api_url = f"https://itch.io/api/1/{self.auth_header}/game/{game_id}/uploads"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            if version_id is not None:
                version_element = None
                for upload in data["uploads"]:
                    if str(upload["id"]) == str(version_id):
                        version_element = upload
                        break
                if version_element is not None:
                    json_string = json.dumps(version_element, indent=4)
                    pyperclip.copy(json_string)
                    self.show_warning('Clipboard', 'Copied the metadata to the clipboard!')
            else:
                for upload in data["uploads"]:
                    json_string = json.dumps(upload, indent=4)
                    pyperclip.copy(json_string)
                    self.show_warning('Clipboard', 'Copied the metadata to the clipboard!')
        else:
            self.show_warning('API Error', 'Unable to fetch data from the API.')

    def extract_ids_paid(self):
        url = self.url_input.text()
        version_id = None
        if "w3g3a5v6.ssl.hwcdn.net" in url:
            match = re.search(r'game/(\d+)/(\d+)', url)
            if match:
                game_id, version_id = match.groups()
        else:
            game_id = self.extract_game_id_from_data_json(url)

        api_url = f"https://itch.io/api/1/{self.auth_header}/my-owned-keys"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            game_owned = False
            for key in data['owned_keys']:
                if str(key["game_id"]) == str(game_id):
                    game_owned = True
                    uploads_api_url = f"https://api.itch.io/games/{game_id}/uploads?download_key_id={key['id']}"
                    headers = {"Authorization": self.auth_header}
                    uploads_response = requests.get(uploads_api_url, headers=headers)
                    
                    if uploads_response.status_code == 200:
                        uploads_data = uploads_response.json()
                        if version_id is not None:
                            version_element = None
                            for upload in uploads_data["uploads"]:
                                if str(upload["id"]) == str(version_id):
                                    version_element = upload
                                    break
                            if version_element is not None:
                                json_string = json.dumps(version_element, indent=4)
                                pyperclip.copy(json_string)
                                self.show_warning('Clipboard', 'Copied the metadata to the clipboard!')

                        else:
                             for upload in uploads_data["uploads"]:
                                json_string = json.dumps(upload, indent=4)
                                pyperclip.copy(json_string)
                                self.show_warning('Clipboard', 'Copied the metadata to the clipboard!')

                    else:
                        self.show_warning('API Error', 'Unable to fetch data from the uploads API.')
                    
                    break
            
            if not game_owned:
                self.show_warning('Game Not Owned', 'The specified game ID is not owned by the user.')
        else:
            self.show_warning('API Error', 'Unable to fetch data from the API.')

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message, QMessageBox.Ok)

class MainApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Choose Operation')
        self.setGeometry(100, 100, 380, 200)

        self.itch_button_free = QPushButton('Extract Itch.io metadata (free)')
        self.itch_button_free.clicked.connect(self.open_itchio_downloader_free)

        self.itch_button_paid = QPushButton('Extract Itch.io metadata (paid)')
        self.itch_button_paid.clicked.connect(self.open_itchio_downloader_paid)

        layout = QVBoxLayout()
        layout.addWidget(self.itch_button_free)
        layout.addWidget(self.itch_button_paid)

        self.setLayout(layout)

    def open_itchio_downloader_free(self):
        self.itchio_downloader = ItchioDownloaderV2()
        self.itchio_downloader.extract_button_paid.setEnabled(False)
        self.itchio_downloader.show()

    def open_itchio_downloader_paid(self):
        self.itchio_downloader = ItchioDownloaderV2()
        self.itchio_downloader.extract_button_free.setEnabled(False)
        self.itchio_downloader.show()

def main():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
