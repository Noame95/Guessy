import tkinter
import protocol
import socket
from ConnectionWindow import ConnectionWindow
from MainWindow import MainWindow
from Crypto.Random import get_random_bytes


class Client:
    def __init__(self):
        self.protocol = protocol.Protocol()
        self.quit = False
        self.connection_window = ConnectionWindow()
        self.main_window = None
        self.aes_key = None
        self.cipher_for_encryption = None
        self.cipher_for_decryption = None
        self.my_socket = None
        self.username = None

    def make_sign_log_req(self, cmd):
        username = self.connection_window.username_val
        password = self.connection_window.password_val
        email = self.connection_window.email_val
        msg = self.protocol.create_msg(cmd, [username, password, email], self.cipher_for_encryption)
        self.my_socket.send(msg)
        validation_msg = self.protocol.get_msg(self.my_socket, self.cipher_for_decryption)
        is_valid, error = validation_msg[2][0], validation_msg[2][1]
        is_valid = False if is_valid == "False" else True
        if is_valid:
            self.connection_window.clear_screen()
            self.username = username
            return True
        else:
            self.connection_window.reset_val(self.connection_window.username_entry)
            self.connection_window.reset_val(self.connection_window.password_entry)
            self.connection_window.reset_val(self.connection_window.email_entry)
            if self.connection_window.error_message:
                self.connection_window.error_message.config(text=error)
            else:
                self.connection_window.error_message = tkinter.Label(
                    self.connection_window.window,
                    text=error,
                    font=('Calibri', 16),
                    fg="red",
                    bg="#f5f5f5"
                )
                self.connection_window.error_message.pack(pady=5)
            self.connection_window.submitted = False
            return False

    def keys(self):
        is_valid, command, msg_parts = self.protocol.get_msg(self.my_socket)
        if is_valid and command == self.protocol.CMDS[2]:
            server_public_key = msg_parts[0]
            self.aes_key = get_random_bytes(self.protocol.KEY_LENGTH)
            print(type(self.aes_key))
            rsa_cipher = self.protocol.get_rsa_cipher(server_public_key)
            crypt_msg = self.protocol.create_msg(self.protocol.CMDS[2], [self.aes_key], rsa_cipher)
            self.my_socket.send(crypt_msg)
            self.cipher_for_encryption = self.protocol.get_aes_cipher(self.aes_key)
            self.cipher_for_decryption = self.protocol.get_aes_cipher(self.aes_key)

    def db_connection(self):
        self.connection_window.window.protocol("WM_DELETE_WINDOW", lambda: self.close_all(self.connection_window))
        try:
            while not self.quit:
                self.connection_window.update()
                if self.connection_window.submitted:
                    if self.connection_window.sign_or_log == self.protocol.CMDS[0]:
                        if self.make_sign_log_req(self.protocol.CMDS[0]):
                            break
                    elif self.connection_window.sign_or_log == self.protocol.CMDS[1]:
                        if self.make_sign_log_req(self.protocol.CMDS[1]):
                            break
        except tkinter.TclError:
            self.quit = True

    def handle_client_requests(self):
        self.main_window.window.protocol("WM_DELETE_WINDOW", lambda: self.close_all(self.main_window))
        while not self.quit:
            try:
                self.main_window.window.update()
            except tkinter.TclError:
                self.quit = True
                break
            self.handle_char_response()
            self.handle_folders_response()

    def handle_char_response(self):
        if self.main_window.uploaded_file_data is not None:
            msg = self.protocol.create_msg(self.protocol.CMDS[4], [len(self.main_window.uploaded_file_data)],
                                           self.cipher_for_encryption)
            self.my_socket.send(msg)
            self.my_socket.send(self.main_window.uploaded_file_data)
            _, _, char = self.protocol.get_msg(self.my_socket, self.cipher_for_decryption)
            reaction = self.main_window.check_char(char)
            if reaction is not None:
                feedback_msg = self.protocol.create_msg(self.protocol.CMDS[6], [reaction], self.cipher_for_encryption)
                self.my_socket.send(feedback_msg)
            self.main_window.uploaded_file_data = None

    def handle_folders_response(self):
        if self.main_window.current_channel == self.main_window.MY_FOLDER_CHANNEL and not self.main_window.has_loaded_files:
            self.main_window.files_list = self.get_file_list(self.username)
            if self.main_window.files_list:
                self.main_window.show_file_thumbnails()
                self.main_window.has_loaded_files = True
        if self.main_window.current_channel == self.main_window.OTHERS_FOLDERS_CHANNEL and not self.main_window.has_loaded_folders:
            folders_msg = self.protocol.create_msg(self.protocol.CMDS[8], [], self.cipher_for_encryption)
            self.my_socket.send(folders_msg)
            self.main_window.folders_list = self.protocol.get_msg(self.my_socket, self.cipher_for_decryption)[2]
            self.main_window.show_other_folders()
            self.main_window.has_loaded_folders = True

        if self.main_window.selected_other_folder_name is not None:
            self.main_window.files_list = self.get_file_list(self.main_window.selected_other_folder_name)
            if self.main_window.files_list:
                self.main_window.show_file_thumbnails()
                self.main_window.has_loaded_files = True
                self.main_window.selected_other_folder_name = None

        if self.main_window.deleted_file is not None:
            del_file_msg = self.protocol.create_msg(self.protocol.CMDS[10], [self.main_window.deleted_file], self.cipher_for_encryption)
            self.my_socket.send(del_file_msg)
            self.main_window.has_loaded_files = False
            self.main_window.deleted_file = None

    def get_file_list(self, username):
        lst = []
        msg = self.protocol.create_msg(self.protocol.CMDS[7], [username],
                                       self.cipher_for_encryption)
        self.my_socket.send(msg)
        msg = self.protocol.get_msg(self.my_socket, self.cipher_for_decryption)
        print(msg)
        if msg[1] == self.protocol.CMDS[9]:
            return msg[2][0]  # the string error itself!
        if msg[1] == self.protocol.CMDS[7]:
            file_names = msg[2]
            file_sizes = self.protocol.get_msg(self.my_socket, self.cipher_for_decryption)[2]
            amount = len(file_names)
            for i in range(amount):
                data = self.protocol.get_file_data(int(file_sizes[i]), self.my_socket)
                lst.append([file_names[i], data])
            return lst

    def destroy_window(self, gui):
        if gui is not None:
            try:
                gui.window.destroy()
            except:
                pass

    def close_all(self, gui):
        self.quit = True
        try:
            self.my_socket.shutdown(socket.SHUT_RDWR)
            self.my_socket.close()
        except:
            pass
        self.destroy_window(gui)

    def main(self):
        self.my_socket = socket.socket()
        try:
            self.my_socket.connect((self.protocol.SERVER_IP, self.protocol.PORT))
            self.keys()
            if self.quit:
                return
            self.db_connection()
            if self.quit:
                return
            self.connection_window.window.destroy()
            self.main_window = MainWindow()
            self.handle_client_requests()
        except (ConnectionResetError, socket.error, OSError):
            self.quit = True
        finally:
            self.destroy_window(self.connection_window)
            self.destroy_window(self.main_window)
            self.my_socket.close()


if __name__ == "__main__":
    client = Client()
    client.main()
