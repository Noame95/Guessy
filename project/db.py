import os
import shutil
import socket
import sqlite3


class DataBase:
    def __init__(self):
        self.DB_FILE_NAME = 'my_database.db'
        self.INVALID_CHARACTERS = r'[<>:"/\\|?*]'
        self.ADDING_TIMES_RIGHT_STR = "times_right"
        self.ADDING_TIMES_WRONG_STR = "times_wrong"
        self.LIKE = "Like"
        self.DISLIKE = "Dislike"
        self.NOTHING = ""

        self.USER_IS_ALREADY_HERE = "This user is already here."
        self.USER_NAME_IS_ALREADY_USED = "Failed to sign up, username exists"
        self.NO_SUCH_USERNAME = "Username doesn't exist."
        self.INCORRECT_PASSWORD = "Incorrect password"
        self.INCORRECT_EMAIL = "Incorrect email"
        self.PASSWORD_CANT_BE_EMPTY = "Password cannot be empty."
        self.USERNAME_CANT_BE_EMPTY = "Username cannot be empty."
        self.INVALID_CHARACTERS_IN_USERNAME = f"Username can't include {self.INVALID_CHARACTERS} in it."
        self.NOT_ENOUGH_CHARACTERS = "There must be only 3-10 characters."
        self.NOT_ENOUGH_NUMBERS = "There must be at least 1 number."
        self.NOT_ENOUGH_LETTERS = "There must be at least 1 letter."
        self.INVALID_EMAIL_FORMAT = "Invalid email format."
        self.NO_SUCH_EMAIL_DOMAIN = "This email domain doesn't even exist."

        self.active_list = []  # [[username, client, enc_key, dec_key, last_file_size], ...]

    def initialize_database(self, folder_name_to_delete):
        if os.path.exists(self.DB_FILE_NAME):
            os.remove(self.DB_FILE_NAME)
        conn = sqlite3.connect(self.DB_FILE_NAME)
        cursor = conn.cursor()

        # Table for user credentials
        cursor.execute('''CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email TEXT NOT NULL
            );''')

        # Table for user stats
        cursor.execute('''CREATE TABLE user_stats (
                username TEXT PRIMARY KEY,
                times_right INTEGER DEFAULT 0,
                times_wrong INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            );''')

        conn.commit()
        conn.close()
        shutil.rmtree(folder_name_to_delete)

    def client_log_in_if_possible(self, username, password, email):
        conn = sqlite3.connect(self.DB_FILE_NAME)
        cursor = conn.cursor()

        if self.is_client_in_list(username):
            conn.close()
            return False, self.USER_IS_ALREADY_HERE

        cursor.execute("SELECT password, email FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return False, self.NO_SUCH_USERNAME

        db_password, db_email = row

        if email != db_email:
            conn.close()
            return False, self.INCORRECT_EMAIL

        if str(password) != db_password:
            conn.close()
            return False, self.INCORRECT_PASSWORD

        conn.close()
        return True, ''

    def client_sign_up_if_possible(self, username, password, email):
        conn = sqlite3.connect(self.DB_FILE_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return False, self.USER_NAME_IS_ALREADY_USED

        if username == self.NOTHING:
            conn.close()
            return False, self.USERNAME_CANT_BE_EMPTY

        if len(username) < 3 or len(username) > 10:
            conn.close()
            return False, self.NOT_ENOUGH_CHARACTERS

        for invalid_char in self.INVALID_CHARACTERS:
            for char in username:
                if invalid_char == char:
                    conn.close()
                    return False, self.INVALID_CHARACTERS_IN_USERNAME

        if password == self.NOTHING:
            conn.close()
            return False, self.PASSWORD_CANT_BE_EMPTY

        if not any(c.isdigit() for c in username):
            conn.close()
            return False, self.NOT_ENOUGH_NUMBERS

        if not any(c.isalpha() for c in username):
            conn.close()
            return False, self.NOT_ENOUGH_LETTERS

        if "@" not in email or "." not in email.split("@")[-1]:
            conn.close()
            return False, self.INVALID_EMAIL_FORMAT

        try:
            domain = email.split('@')[1]
            socket.gethostbyname(domain)
        except Exception:
            conn.close()
            return False, self.NO_SUCH_EMAIL_DOMAIN

        cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
        cursor.execute('INSERT INTO user_stats (username) VALUES (?)', (username,))
        conn.commit()
        conn.close()
        return True, ''

    def increment_times(self, username, times_str):
        conn = sqlite3.connect(self.DB_FILE_NAME)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE user_stats SET {times_str} = {times_str} + 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()

    def is_client_in_list(self, username):
        print(self.active_list)
        for client_info in self.active_list:
            if username == client_info[0]:
                return True
        return False

    def set_username(self, username, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                client_info[0] = username

    def remove_client(self, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                self.active_list.remove(client_info)
                print(client_info)

    def get_username_of_client(self, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                return client_info[0]

    def get_decryption_aes(self, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                return client_info[3]

    def get_encryption_aes(self, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                return client_info[2]

    def get_last_file_size(self, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                return client_info[4]

    def set_last_file_size(self, size, client_socket):
        for client_info in self.active_list:
            if client_socket in client_info:
                client_info[4] = size
