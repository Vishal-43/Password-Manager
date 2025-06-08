from cryptography.fernet import Fernet
import os
import databse # Assuming databse.py is in the same directory

# Initialize the database connection
db = databse.Database()

class PasswordManager:
    """
    Manages encryption and decryption of passwords, and interacts with the
    database for storing and retrieving password entries.
    """
    def __init__(self):
        """
        Initializes the Fernet encryption key.
        If the key file doesn't exist or is empty, a new key is generated and saved.
        """
        self.KEY_FILE = "key.key"
        key = None
        try:
            # Check if the key file exists and is not empty
            if os.path.exists(self.KEY_FILE) and os.path.getsize(self.KEY_FILE) > 0:
                with open(self.KEY_FILE, "rb") as key_file:
                    key = key_file.read()
            
            # If no key was read (file doesn't exist or was empty), generate a new one
            if not key:
                key = Fernet.generate_key()
                with open(self.KEY_FILE, "wb") as kf:
                    kf.write(key)
                print("🔑 Generated a new encryption key and saved it to key.key.")
            else:
                print("🔑 Loaded existing encryption key from key.key.")

        except Exception as e:
            print(f"❌ Error loading or generating encryption key: {e}")
            # Fallback: If any unexpected error occurs during file operations, generate a new key
            # This might lead to inability to decrypt old passwords if the error implies corruption
            key = Fernet.generate_key()
            with open(self.KEY_FILE, "wb") as kf:
                kf.write(key)
            print("🔑 Recovered by generating a new encryption key due to an error.")
        
        # Initialize the Fernet cipher with the loaded or generated key
        self.fernet = Fernet(key)

    def encrypt_password(self, password: str) -> bytes:
        """
        Encrypts a plaintext password.
        Args:
            password (str): The plaintext password to encrypt.
        Returns:
            bytes: The encrypted password as bytes.
        """
        return self.fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password: bytes) -> str:
        """
        Decrypts an encrypted password.
        Args:
            encrypted_password (bytes): The encrypted password as bytes.
        Returns:
            str: The decrypted plaintext password.
        Raises:
            ValueError: If decryption fails (e.g., invalid key or token).
        """
        try:
            return self.fernet.decrypt(encrypted_password).decode()
        except Exception as e:
            # Catching a broader exception to specifically report decryption issues
            print(f"Decryption error for provided data: {e}")
            raise ValueError("Failed to decrypt password. The data might be corrupted or the encryption key has changed.")

    def add_password(self, user_id: int, website: str, username: str, raw_password: str):
        """
        Encrypts a raw password and saves it to the database for a given user.
        Args:
            user_id (int): The ID of the user.
            website (str): The website associated with the password.
            username (str): The username for the website.
            raw_password (str): The plaintext password.
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            encrypted_password = self.encrypt_password(raw_password)
            return db.save_password(user_id, website, username, encrypted_password)
        except Exception as e:
            return False, f"Error encrypting or saving password: {e}"

    def get_passwords(self, user_id: int):
        """
        Retrieves all password entries for a user from the database and decrypts them.
        Args:
            user_id (int): The ID of the user.
        Returns:
            tuple: (success: bool, data: Union[list, str])
                   On success, data is a list of dictionaries with decrypted password details.
                   On failure, data is an error message.
        """
        success, data = db.list_passwords(user_id)
        if not success:
            return False, data # data contains the error message

        decrypted_passwords = []
        for p_entry in data:
            try:
                decrypted_pass = self.decrypt_password(p_entry["encrypted_password"])
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": decrypted_pass # Store as decrypted for frontend
                })
            except ValueError as ve: # Catch specific ValueError from decrypt_password
                print(f"Skipping password for website {p_entry.get('website', 'N/A')} due to decryption error: {ve}")
                # Provide a clear message to the user that the password couldn't be decrypted
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": "[Decryption Failed - Key Mismatch/Corruption]" 
                })
            except Exception as e: # Catch any other unexpected errors during processing
                print(f"An unexpected error occurred for website {p_entry.get('website', 'N/A')}: {e}")
                decrypted_passwords.append({
                    "id": p_entry["id"],
                    "website": p_entry["website"],
                    "username": p_entry["username"],
                    "password": "[Processing Error]" 
                })
        return True, decrypted_passwords

    def delete_password(self, password_id: int, user_id: int):
        """
        Deletes a specific password entry from the database.
        Args:
            password_id (int): The ID of the password entry to delete.
            user_id (int): The ID of the user who owns the password.
        Returns:
            tuple: (success: bool, message: str)
        """
        return db.delete_password(password_id, user_id)

pm = PasswordManager()

password = b'gAAAAABoRaBvLdrh97_C5kKv_1kSzp5iP5xkSX7uoronJyKPM9Kw0mIn8V4aq33iI-FKgfuFbgM7o3t9U7GEQzjFOA_yW8O2ug=='
print(pm.decrypt_password(password))

