import hashlib
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA


class Protocol:
    def __init__(self):
        self.PORT = 8818
        self.BINDING_IP = '0.0.0.0'
        self.SERVER_IP = "192.168.1.60"
        self.KEY_LENGTH = 16
        self.SEPARATOR = "***"
        self.LENGTH_FIELD_SIZE = 10
        self.CMDS = ["SIGNUP",
                     "LOGIN",
                     "CRYPT",
                     "VALIDATION",
                     "REQUEST",
                     "ANSWER",
                     "FEEDBACK",
                     "FILES",
                     "FOLDERS",
                     "ERROR",
                     "DELETE"]

    def check_cmd(self, cmd):
        return cmd in self.CMDS

    def create_msg(self, cmd, msg_parts, key=None):
        if self.check_cmd(cmd):
            msg = cmd
            for part in msg_parts:
                msg += self.SEPARATOR + str(part)
            raw_msg = msg.encode()
            if key:
                encrypted_msg = self.encrypt_message(raw_msg.decode(), key)
                length_field = str(len(encrypted_msg)).zfill(self.LENGTH_FIELD_SIZE).encode()
                return length_field + encrypted_msg
            else:
                length_field = str(len(raw_msg)).zfill(self.LENGTH_FIELD_SIZE).encode()
                return length_field + raw_msg

    def get_msg(self, sockett, cipher=None):
        length_field = sockett.recv(self.LENGTH_FIELD_SIZE)
        if not length_field:
            return False, "", ""
        length = int(length_field.decode())
        encrypted_data = sockett.recv(length)
        while len(encrypted_data) < length:
            encrypted_data += sockett.recv(length - len(encrypted_data))
        if cipher:
            decrypted_data = self.decrypt_message(encrypted_data, cipher)
            msg = decrypted_data.decode()
        else:
            msg = encrypted_data.decode()

        command = msg.split(self.SEPARATOR)[0]
        lst = msg.split(self.SEPARATOR)[1::]
        if command == self.CMDS[2]: # when we get a key there is a problem decoding it normally...
            lst[0] = lst[0][2:len(lst[0]) - 1].encode()
            lst[0] = lst[0].replace(b'\\n', b'\n')
        return True, command, lst

    def pad(self, s):
        padding_length = self.KEY_LENGTH - len(s) % self.KEY_LENGTH
        padding = chr(padding_length) * padding_length
        return s + padding

    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def get_aes_cipher(self, key):
        key = hashlib.sha256(key).digest()  # Making the key 32 bytes long
        return AES.new(key, AES.MODE_CBC, iv=key[:self.KEY_LENGTH])  # Using the first 16 bytes of the key

    def encrypt_message(self, message, cipher):
        return cipher.encrypt(self.pad(message).encode())

    def decrypt_message(self, message, cipher):
        return self.unpad(cipher.decrypt(message))

    # RSA functions
    def generate_rsa_keys(self):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        return private_key, public_key

    def get_rsa_cipher(self, public_key):
        rsa_key = RSA.import_key(public_key)
        return PKCS1_OAEP.new(rsa_key)

    def rsa_encrypt_message(self, message, rsa_cipher):
        return rsa_cipher.encrypt(message)

    def rsa_decrypt_message(self, encrypted_message, private_key):
        rsa_key = RSA.import_key(private_key)
        rsa_cipher = PKCS1_OAEP.new(rsa_key)
        return rsa_cipher.decrypt(encrypted_message)

    def get_file_data(self, size, my_other_socket):
        received_data = b''
        while len(received_data) < size:
            chunk = my_other_socket.recv(size - len(received_data))
            if not chunk:
                break
            else:
                received_data += chunk
        return received_data

    def pad_bytes(self, b):
        padding_length = self.KEY_LENGTH - len(b) % self.KEY_LENGTH
        padding = bytes([padding_length] * padding_length)
        return b + padding

    def unpad_bytes(self, b):
        padding_length = b[-1]
        return b[:-padding_length]

    def encrypt_bytes(self, data, cipher):
        return cipher.encrypt(self.pad_bytes(data))

    def decrypt_bytes(self, encrypted_data, cipher):
        return self.unpad_bytes(cipher.decrypt(encrypted_data))