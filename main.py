from cryptography.fernet import Fernet
import os
import databse  # Assuming databse.py is in the same directory
import binascii

# Initialize the database connection
db = databse.Database()

class PasswordManager:
    """
    Manages encryption and decryption of passwords, and interacts with the
    database for storing and retrieving password entries.
    """
    def __init__(self):
        self.KEY_FILE = "key.key"
        key = None
        try:
            if os.path.exists(self.KEY_FILE) and os.path.getsize(self.KEY_FILE) > 0:
                with open(self.KEY_FILE, "rb") as key_file:
                    key = key_file.read()
            if not key:
                key = Fernet.generate_key()
                with open(self.KEY_FILE, "wb") as kf:
                    kf.write(key)
                print("🔑 Generated a new encryption key and saved it to key.key.")
            else:
                print("🔑 Loaded existing encryption key from key.key.")
        except Exception as e:
            print(f"❌ Error loading or generating encryption key: {e}")
            key = Fernet.generate_key()
            with open(self.KEY_FILE, "wb") as kf:
                kf.write(key)
            print("🔑 Recovered by generating a new encryption key due to an error.")

        self.fernet = Fernet(key)

    def encrypt_password(self, password: str) -> bytes:
        return self.fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password: bytes) -> str:
        try:
            return self.fernet.decrypt(encrypted_password).decode()
        except Exception as e:
            print(f"Decryption error for provided data: {e}")
            raise ValueError("Failed to decrypt password. The data might be corrupted or the encryption key has changed.")

    def add_password(self, user_id: int, website: str, username: str, raw_password: str):
        try:
            print(raw_password)
            encrypted_password = self.encrypt_password(raw_password)
            print(encrypted_password)
            return db.save_password(user_id, website, username, encrypted_password)
        except Exception as e:
            return False, f"Error encrypting or saving password: {e}"

    def get_passwords(self, user_id: int):
        success, data = db.list_passwords(user_id)
        if not success:
            return False, data

        decrypted_passwords = []
        for p_entry in data:
            try:
                raw = p_entry["encrypted_password"]

                # Decode from hex if PostgreSQL returned a hex string (BYTEA behavior)
                if isinstance(raw, str):
                    raw = binascii.unhexlify(raw[2:] if raw.startswith('\\x') else raw)

                decrypted_pass = self.decrypt_password(raw)
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": decrypted_pass
                })
            except ValueError as ve:
                print(f"Skipping password for website {p_entry.get('website', 'N/A')} due to decryption error: {ve}")
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": "[Decryption Failed - Key Mismatch/Corruption]"
                })
            except Exception as e:
                print(f"Unexpected error for website {p_entry.get('website', 'N/A')}: {e}")
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": "[Processing Error]"
                })

        return True, decrypted_passwords

    def delete_password(self, password_id: int, user_id: int):
        return db.delete_password(password_id, user_id)

    def update_password(self, password_id: int, user_id: int, website: str, username: str, raw_password: str = None) -> tuple[bool, str]:
        
        try:
            print(raw_password)
            encrypted_password = self.encrypt_password(raw_password)
            print(encrypted_password)
            return db.update_password(password_id, user_id, website, username, encrypted_password)
        except Exception as e:
            return False, f"Error encrypting or saving password: {e}"
# For testing
pm = password_manager = PasswordManager()

pm.add_password(1, "example.com", "user1", "password123")
