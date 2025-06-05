import os
from cryptography.fernet import Fernet
from pymongo import MongoClient, errors as pymongo_errors
from pymongo.collection import Collection
from bson import Binary # For storing encrypted bytes

class PasswordManagerMongo:
    """
    Manages passwords by storing them encrypted in a MongoDB database.
    """
    def __init__(self, 
                 connection_string=os.getenv("MONGO_URI"), 
                 db_name="password_manager_db", 
                 collection_name="passwords_collection", 
                 key_file_name="mongo_key.key"):
        """
        Initializes the PasswordManagerMongo.
        Sets up the MongoDB connection, gets the database and collection,
        ensures necessary indexes, and loads or generates an encryption key.

        Args:
            connection_string (str): MongoDB connection string.
            db_name (str): Name of the database to use.
            collection_name (str): Name of the collection to store passwords.
            key_file_name (str): Name of the file to store the encryption key.
        """
        self.key_file_path = key_file_name
        self.client = None # Initialize client to None

        try:
            # Initialize MongoDB client and connect
            self.client = MongoClient(connection_string)
            # Ping the server to verify connection
            self.client.admin.command('ping') 
            # print("Successfully connected to MongoDB!") # For debugging
        except pymongo_errors.ConnectionFailure as e:
            print(f"MongoDB connection error: Could not connect to server at {connection_string}. Error: {e}")
            # Propagate the error or handle it by setting a state that prevents operations
            raise  # Or set self.client = None and check in methods

        self.db = self.client[db_name]
        self.collection: Collection = self.db[collection_name] # Type hint for better autocompletion

        self._ensure_indexes()
        self._load_or_generate_key()

    def _ensure_indexes(self):
        """Ensures that necessary indexes are created on the collection."""
        try:
            # Create an index on 'website' for faster lookups.
            # Can be unique if you want to enforce one entry per website.
            # For this migration, keeping it non-unique to match SQLite behavior.
            self.collection.create_index("website", background=True)
            # print(f"Index on 'website' ensured for collection '{self.collection.name}'.") # For debugging
        except pymongo_errors.OperationFailure as e:
            print(f"Error creating index on 'website': {e}")
            # This might not be critical for functionality but impacts performance.

    def _load_or_generate_key(self):
        """Loads an existing encryption key or generates a new one if not found."""
        try:
            if os.path.exists(self.key_file_path) and os.path.getsize(self.key_file_path) > 0:
                with open(self.key_file_path, "rb") as key_file_handle:
                    key = key_file_handle.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file_path, "wb") as key_file_handle:
                    key_file_handle.write(key)
                # Consider setting file permissions for the key file to restrict access
                # os.chmod(self.key_file_path, 0o600) # Example for Unix-like systems
        except IOError as e:
            print(f"Error loading/saving encryption key from '{self.key_file_path}': {e}")
            raise
        
        try:
            self.f = Fernet(key)
        except Exception as e: 
            print(f"Error initializing Fernet with key: {e}")
            raise

    def add_password(self, website, username, password):
        """
        Adds a new password entry to the MongoDB collection.
        The password is encrypted before storage.

        Args:
            website (str): The website for the password.
            username (str): The username for the website.
            password (str): The password to store.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not all([website, username, password]):
            print("Error: Website, username, and password cannot be empty.")
            return False

        if not self.client:
            print("Error: MongoDB client not initialized. Cannot add password.")
            return False

        try:
            encrypted_password_bytes = self.f.encrypt(password.encode('utf-8'))
            # Store encrypted password as BSON Binary type
            encrypted_password_bson = Binary(encrypted_password_bytes) 
            
            password_document = {
                "website": website,
                "username": username,
                "password": encrypted_password_bson # Storing as BSON Binary
            }
            self.collection.insert_one(password_document)
            return True
        except pymongo_errors.PyMongoError as e: # Catch generic PyMongo errors
            print(f"MongoDB error while adding password for '{website}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while adding password for '{website}': {e}")
            return False

    def get_password(self, website):
        """
        Retrieves and decrypts the password for a given website from MongoDB.

        Args:
            website (str): The website to retrieve the password for.

        Returns:
            tuple: (username, decrypted_password) if found, else None.
        """
        if not website:
            print("Error: Website cannot be empty.")
            return None
        
        if not self.client:
            print("Error: MongoDB client not initialized. Cannot get password.")
            return None

        try:
            result_doc = self.collection.find_one({"website": website})
            if result_doc:
                username = result_doc["username"]
                # Encrypted password is BSON Binary, convert back to bytes for decryption
                encrypted_password_bytes = result_doc["password"] # This is already bytes if stored as Binary
                decrypted_password = self.f.decrypt(encrypted_password_bytes).decode('utf-8')
                return username, decrypted_password
            else:
                return None
        except pymongo_errors.PyMongoError as e:
            print(f"MongoDB error while getting password for '{website}': {e}")
            return None
        except (Fernet.InvalidToken, TypeError, ValueError) as e:
            print(f"Error decrypting password for '{website}'. Key might be incorrect or data corrupted: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while retrieving password for '{website}': {e}")
            return None

    def delete_password(self, website):
        """
        Deletes a password entry for a given website from MongoDB.

        Args:
            website (str): The website to delete the password for.

        Returns:
            bool: True if deletion was successful (document found and deleted), 
                  False if document not found or an error occurred.
        """
        if not website:
            print("Error: Website cannot be empty.")
            return False

        if not self.client:
            print("Error: MongoDB client not initialized. Cannot delete password.")
            return False

        try:
            result = self.collection.delete_one({"website": website})
            return result.deleted_count > 0 # True if one document was deleted
        except pymongo_errors.PyMongoError as e:
            print(f"MongoDB error while deleting password for '{website}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while deleting password for '{website}': {e}")
            return False

    def list_passwords(self):
        """
        Lists all stored website, username, and decrypted passwords from MongoDB.

        Returns:
            list: A list of tuples (website, username, decrypted_password).
                  Returns an empty list if no passwords are stored or on error.
        """
        if not self.client:
            print("Error: MongoDB client not initialized. Cannot list passwords.")
            return []
            
        passwords_list = []
        try:
            for doc in self.collection.find({}):
                try:
                    decrypted_password = self.f.decrypt(doc["password"]).decode('utf-8')
                    passwords_list.append((doc["website"], doc["username"], decrypted_password))
                except (Fernet.InvalidToken, TypeError, ValueError) as e:
                    print(f"Could not decrypt password for '{doc['website']}' while listing: {e}. Skipping.")
                    passwords_list.append((doc["website"], doc["username"], "[DECRYPTION FAILED]"))
            return passwords_list
        except pymongo_errors.PyMongoError as e:
            print(f"MongoDB error while listing passwords: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while listing passwords: {e}")
            return []

    def search_passwords(self, search_query):
        """
        Searches for passwords in MongoDB where the website name matches the search query (case-insensitive regex).

        Args:
            search_query (str): The term to search for in website names.

        Returns:
            list: A list of matching (website, username, decrypted_password) tuples.
                  Returns an empty list if no matches or on error.
        """
        if not search_query:
            print("Error: Search query cannot be empty.")
            return []

        if not self.client:
            print("Error: MongoDB client not initialized. Cannot search passwords.")
            return []
            
        passwords_list = []
        try:
            # Using regex for a 'LIKE %query%' equivalent, 'i' for case-insensitive
            query_filter = {"website": {"$regex": search_query, "$options": "i"}}
            for doc in self.collection.find(query_filter):
                try:
                    decrypted_password = self.f.decrypt(doc["password"]).decode('utf-8')
                    passwords_list.append((doc["website"], doc["username"], decrypted_password))
                except (Fernet.InvalidToken, TypeError, ValueError) as e:
                    print(f"Could not decrypt password for '{doc['website']}' during search: {e}. Skipping.")
                    passwords_list.append((doc["website"], doc["username"], "[DECRYPTION FAILED]"))
            return passwords_list
        except pymongo_errors.PyMongoError as e:
            print(f"MongoDB error while searching passwords for query '{search_query}': {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while searching passwords for query '{search_query}': {e}")
            return []

    def close(self):
        """Closes the MongoDB client connection if it's open."""
        if self.client:
            try:
                self.client.close()
                # print("MongoDB connection closed.") # Optional: for debugging
            except Exception as e: # Catch generic exception during close
                print(f"Error closing MongoDB connection: {e}")
            finally:
                self.client = None # Ensure client is marked as None

    def __enter__(self):
        # The connection is established in __init__.
        # This method allows the class to be used in a 'with' statement.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close the connection when exiting the 'with' block.
        self.close()
