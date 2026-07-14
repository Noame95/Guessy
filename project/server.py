import socket
import threading
from protocol import Protocol
from threading import Thread
from ai import Model
from db import DataBase
import os
import re


class Server:
    def __init__(self):
        self.protocol = Protocol()
        self.server_socket = socket.socket()
        self.server_model = Model()
        self.db = DataBase()
        self.run = True
        self.lock = threading.Lock()
        self.PRIVATE_KEY, self.PUBLIC_KEY = self.protocol.generate_rsa_keys()
        self.SERVER_FOLDER = "Results"
        self.NO_FILES = "There are no files here."

    def handle_client(self, client_socket):
        try:
            client_socket.send(self.protocol.create_msg(self.protocol.CMDS[2], [self.PUBLIC_KEY]))
            client_aes_decryption_key = self.protocol.get_rsa_cipher(self.PRIVATE_KEY)
            client_aes_encryption_key = None
            while self.run:
                size = self.db.get_last_file_size(client_socket)
                if size is None or size == 0:
                    valid, command, msg_list = self.protocol.get_msg(client_socket, client_aes_decryption_key)
                    if self.protocol.check_cmd(command) and valid:
                        valid = self.handle_response(client_socket, command, msg_list,
                                                     client_aes_encryption_key)
                        if client_aes_encryption_key is None:
                            client_aes_decryption_key = self.db.get_decryption_aes(client_socket)
                            client_aes_encryption_key = self.db.get_encryption_aes(client_socket)
                        if not valid:
                            continue
                else:
                    self.handle_file_upload(client_socket, size)
                    self.db.set_last_file_size(0, client_socket)

        except (ConnectionResetError, socket.error, OSError):
            self.db.remove_client(client_socket)

    def handle_response(self, client_socket, command, msg_list, aes_key=None):
        print(command, msg_list)
        if command == self.protocol.CMDS[0]:  # signup
            self.handle_connection(client_socket, self.db.client_sign_up_if_possible, msg_list, aes_key)

        if command == self.protocol.CMDS[1]:  # login
            self.handle_connection(client_socket, self.db.client_log_in_if_possible, msg_list, aes_key)

        if command == self.protocol.CMDS[2]:  # crypt
            aes_key = bytes(msg_list[0].decode('unicode_escape'), 'latin1')
            self.db.active_list.append([self.db.NOTHING, client_socket, self.protocol.get_aes_cipher(aes_key), self.protocol.get_aes_cipher(aes_key), 0])

        if command == self.protocol.CMDS[4]:  # request
            size = int(msg_list[0])
            self.db.set_last_file_size(size, client_socket)

        if command == self.protocol.CMDS[6]:  # feedback
            feedback = msg_list[0]
            print(feedback)
            if feedback == self.db.LIKE:
                self.db.increment_times(self.db.get_username_of_client(client_socket), self.db.ADDING_TIMES_RIGHT_STR)
            if feedback == self.db.DISLIKE:
                self.db.increment_times(self.db.get_username_of_client(client_socket), self.db.ADDING_TIMES_WRONG_STR)

        if command == self.protocol.CMDS[7]:  # files
            username = msg_list[0]
            names, sizes, datas = self.get_user_files_info(username)
            if names and sizes and datas:
                names_msg = self.protocol.create_msg(self.protocol.CMDS[7], names, self.db.get_encryption_aes(client_socket))
                client_socket.send(names_msg)
                sizes_msg = self.protocol.create_msg(self.protocol.CMDS[7], sizes, self.db.get_encryption_aes(client_socket))
                client_socket.send(sizes_msg)
                for i in range(len(sizes)):
                    client_socket.send(datas[i])
            else:
                no_files_msg = self.protocol.create_msg(self.protocol.CMDS[9], [self.NO_FILES], self.db.get_encryption_aes(client_socket))
                client_socket.send(no_files_msg)

        if command == self.protocol.CMDS[8]: # folders
            folder_list = self.get_all_user_dirs(self.db.get_username_of_client(client_socket))
            folders_msg = self.protocol.create_msg(self.protocol.CMDS[8], folder_list, self.db.get_encryption_aes(client_socket))
            client_socket.send(folders_msg)

        if command == self.protocol.CMDS[10]:  # delete
            file_path = msg_list[0]
            username = self.db.get_username_of_client(client_socket)
            full_file_path = os.path.join(self.SERVER_FOLDER, username, file_path)
            os.remove(full_file_path)
            self.sort_files(client_socket)
        return True

    def handle_file_upload(self, client_socket, file_size):
        data = self.protocol.get_file_data(file_size, client_socket)
        char = self.server_model.use_model(data)
        msg = self.protocol.create_msg(self.protocol.CMDS[5], [char], self.db.get_encryption_aes(client_socket))
        client_socket.send(msg)
        username = self.db.get_username_of_client(client_socket)
        user_dir = os.path.join(self.SERVER_FOLDER, username)
        pattern = re.compile(rf"^{char}_(\d+)\.png$")
        max_index = 0
        for filename in os.listdir(user_dir):
            match = pattern.match(filename)
            if match:
                index = int(match.group(1))
                max_index = max(max_index, index)
        new_index = max_index + 1
        file_path = os.path.join(user_dir, f"{char}_{new_index}.png")
        with open(file_path, "wb") as f:
            f.write(data)

    def sort_files(self, client_socket):
        username = self.db.get_username_of_client(client_socket)
        user_dir = os.path.join(self.SERVER_FOLDER, username)
        pattern = re.compile(r"^(.+?)_(\d+)\.png$")
        files_by_char = {}
        for filename in os.listdir(user_dir):
            match = pattern.match(filename)
            if match:
                char = match.group(1)
                index = int(match.group(2))
                if char not in files_by_char:
                    files_by_char[char] = []
                files_by_char[char].append((index, filename))
        for char, files in files_by_char.items():
            files.sort()
            for new_index, (_, filename) in enumerate(files, start=1):
                old_path = os.path.join(user_dir, filename)
                new_filename = f"{char}_{new_index}.png"
                new_path = os.path.join(user_dir, new_filename)
                if old_path != new_path:
                    os.rename(old_path, new_path)

    def get_user_files_info(self, username):
        user_dir = os.path.join(self.SERVER_FOLDER, username)
        filenames = []
        sizes = []
        datas = []
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                    filenames.append(filename)
                    sizes.append(str(len(data)))
                    datas.append(data)
        return filenames, sizes, datas

    def get_all_user_dirs(self, username):
        return [name for name in os.listdir(self.SERVER_FOLDER)
                if os.path.isdir(os.path.join(self.SERVER_FOLDER, name)) and name != username]

    def handle_connection(self, client_socket, func, msg_list, aes_key=None):
        username = msg_list[0]
        password = msg_list[1]
        email = msg_list[2]
        with self.lock:
            valid, message = func(username, password, email)
            print(valid)
        client_socket.send(self.protocol.create_msg(self.protocol.CMDS[3], [valid, message], aes_key))
        if valid:
            self.db.set_username(username, client_socket)
            user_dir = os.path.join(self.SERVER_FOLDER, username)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

    def main(self):
        if not os.path.exists(self.SERVER_FOLDER):
            os.makedirs(self.SERVER_FOLDER)
        # self.db.initialize_database(self.SERVER_FOLDER)
        print("server start")
        self.server_socket.bind((self.protocol.BINDING_IP, self.protocol.PORT))
        self.server_socket.listen(0)
        if not os.path.exists(self.SERVER_FOLDER):
            os.makedirs(self.SERVER_FOLDER)
        while self.run:
            try:
                client_socket, client_address = self.server_socket.accept()
                print("New client connected:", client_address)
                client_thread = Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except OSError:
                break


if __name__ == "__main__":
    s = Server()
    s.main()
