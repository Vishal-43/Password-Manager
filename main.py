import databse

from cryptography.fernet import Fernet
db = databse.Database()
class PasswordManager:
    def __init__(self):
         # Load or generate encryption key
        self.KEY_FILE = "key.key"
        try:
            with open(self.KEY_FILE, "rb") as key_file:
                key = key_file.read()
                if not key:
                    key = Fernet.generate_key()
                    with open(self.KEY_FILE, "wb") as key_file:
                        key_file.write(key)
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(self.KEY_FILE, "wb") as key_file:
                key_file.write(key)

        self.f = Fernet(key)

    def add_password(self, website, username, password):
        encrypted_password = self.f.encrypt(password.encode())
        res = db.save_password(website,username,encrypted_password)
        if not res[0]:
            return False
        return True

    def get_password(self, website):
        result = db.get_password(website)
        if result[0]:
            decrypted_password = self.f.decrypt(result[1]["encrypted_password"]).decode()
            return result[0], decrypted_password
        else:
            return False, "Password not found."

    def delete_password(self, id, user_id):
        result  = db.delete_password(id, user_id)
        if result[0]:
            return True , "password deleted sucessfully"
        else:
            return False, result[1]

    def list_passwords(self,user_id):
        return db.list_passwords(user_id)

    
    

