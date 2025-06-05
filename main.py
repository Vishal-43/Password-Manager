import sqlite3
from cryptography.fernet import Fernet


class PasswordManager:
    def __init__(self):
        # Initialize database
        self.conn = sqlite3.connect('password.db')
        self.cour = self.conn.cursor()

        # Create table if not exists
        self.cour.execute('''CREATE TABLE IF NOT EXISTS passwords
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              website TEXT NOT NULL,
                              username TEXT NOT NULL,
                              password TEXT NOT NULL)''')
        self.conn.commit()

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
        if not website or not username or not password:
            return False

        encrypted_password = self.f.encrypt(password.encode())
        self.cour.execute("INSERT INTO passwords (website, username, password) VALUES (%s,%s,%s)",
                          (website, username, encrypted_password))
        self.conn.commit()
        return True

    def get_password(self, website):
        self.cour.execute("SELECT username, password FROM passwords WHERE website = %s", (website,))
        result = self.cour.fetchone()
        if result:
            decrypted_password = self.f.decrypt(result[1]).decode()
            return result[0], decrypted_password
        else:
            return None

    def delete_password(self, website):
        self.cour.execute("DELETE FROM passwords WHERE website = %s", (website,))
        self.conn.commit()
        return True

    def list_passwords(self):
        self.cour.execute("SELECT website, username, password FROM passwords")
        results = self.cour.fetchall()
        passwords = []
        for row in results:
            decrypted_password = self.f.decrypt(row[2]).decode()
            passwords.append((row[0], row[1], decrypted_password))
        return passwords

    def search_passwords(self, search_query):
        self.cour.execute("SELECT website, username, password FROM passwords WHERE website LIKE %s", ('%' + search_query + '%',))
        results = self.cour.fetchall()
        passwords = []
        for row in results:
            decrypted_password = self.f.decrypt(row[2]).decode()
            passwords.append((row[0], row[1], decrypted_password))
        return passwords
    

