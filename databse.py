import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables from .env file
load_dotenv()

class Database:
    """
    A class to manage MongoDB database operations for user authentication.
    It connects to MongoDB Atlas using a connection string from environment variables.
    """
    def __init__(self):
        """
        Initializes the Database class and establishes a connection to MongoDB Atlas.
        It retrieves the MONGO_URI and an optional MONGO_DB_NAME from environment variables.
        """
        self.client = None
        self.db = None
        self.users_collection = None
        self._connect() # Attempt to connect immediately upon instantiation

    def _connect(self):
        """
        Establishes a connection to MongoDB Atlas.
        Retrieves MONGO_URI and MONGO_DB_NAME from environment variables.
        """
        try:
            # Get the MongoDB connection URI from environment variables
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI environment variable not set. Please add it to your .env file.")

            # Initialize the MongoDB client
            self.client = MongoClient(mongo_uri)

            # Get the database instance. The database name can be specified in the MONGO_URI
            # or explicitly retrieved using get_database(). We'll use an env variable for flexibility.
            db_name = os.getenv("MONGO_DB_NAME", "user_auth_db") # Default to 'user_auth_db' if not set
            self.db = self.client.get_database(db_name)

            # Get the specific collection for users
            self.users_collection = self.db.get_collection("users")

            # The ismaster command is a simple way to check if the connection is alive and authenticated.
            self.client.admin.command('ping') # Using 'ping' for a more direct check
            print(f"✅ Connected to MongoDB Atlas database '{db_name}' successfully.")

        except ConnectionFailure as e:
            print(f"❌ MongoDB connection error: {e}")
            self.client = None
            self.db = None
            self.users_collection = None
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            self.client = None
            self.db = None
            self.users_collection = None
        except Exception as e:
            print(f"❌ An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            self.db = None
            self.users_collection = None

    def close_connection(self):
        """
        Closes the MongoDB client connection if it's open.
        """
        if self.client:
            self.client.close()
            print("🔒 MongoDB connection closed.")
            self.client = None
            self.db = None
            self.users_collection = None

    def _check_connection(self):
        """
        Internal helper method to check if the MongoDB connection is established.
        Returns True if connected, False otherwise.
        """
        if not self.client or not self.db or not self.users_collection:
            print("❌ Database connection is not established. Please check MONGO_URI and network access.")
            return False
        return True

    def create_user(self, username, email, password, verification_status):
        """
        Creates a new user record in the MongoDB 'users' collection.
        Checks if a user with the given email already exists to prevent duplicates.

        Args:
            username (str): The username for the new user.
            email (str): The email address (must be unique).
            password (str): The user's password (should be hashed in a real application).
            verification_status (str): The initial verification status (e.g., 'pending', 'verified').

        Returns:
            list: A list containing a boolean (True for success, False for failure)
                  and a string message.
        """
        if not self._check_connection():
            return [False, "Database not connected."]

        try:
            # Check if email already exists
            existing_user = self.users_collection.find_one({"email": email})
            if existing_user:
                print(f"Email '{email}' is already registered.")
                return [False, "Email is already registered."]
            else:
                # Prepare user data to be inserted
                user_data = {
                    "username": username,
                    "email": email,
                    "password": password, # IMPORTANT: In a real application, hash this password (e.g., using bcrypt)!
                    "verification_status": verification_status
                }
                # Insert the new user document
                self.users_collection.insert_one(user_data)
                print(f"User '{username}' with email '{email}' registered successfully!")
                return [True, "User registered successfully."]
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during user creation: {e}")
            return [False, str(e)]
        except Exception as e:
            print(f"❌ An unexpected error occurred during user creation: {e}")
            return [False, str(e)]

    def check_verification_status(self, email):
        """
        Checks the verification status of a user based on their email.

        Args:
            email (str): The email of the user to check.

        Returns:
            str or False: The verification status string (e.g., 'pending', 'verified')
                          if found, otherwise False.
        """
        if not self._check_connection():
            return False
        try:
            user = self.users_collection.find_one({"email": email})
            if user:
                status = user.get("verification_status")
                print(f"Verification status for '{email}': {status}")
                return status
            else:
                print(f"User with email '{email}' not found.")
                return False
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during status check: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred during status check: {e}")
            return False

    def update_verification_status(self, email, verification_status):
        """
        Updates the verification status for a user.

        Args:
            email (str): The email of the user to update.
            verification_status (str): The new verification status.

        Returns:
            bool: True if the status was updated successfully, False otherwise.
        """
        if not self._check_connection():
            return False
        try:
            # Update the document that matches the email
            result = self.users_collection.update_one(
                {"email": email},
                {"$set": {"verification_status": verification_status}}
            )
            if result.matched_count > 0:
                print(f"Verification status for '{email}' updated successfully to '{verification_status}'!")
                return True
            else:
                print(f"User with email '{email}' not found for status update.")
                return False
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during status update: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred during status update: {e}")
            return False

    def get_user(self, email):
        """
        Retrieves the password of a user if their email is verified.

        Args:
            email (str): The email of the user.

        Returns:
            str or False: The user's password string if the user is found and verified,
                          otherwise False.
        """
        if not self._check_connection():
            return False
        try:
            # Find a user where email matches and verification_status is 'verified'
            user = self.users_collection.find_one(
                {"email": email, "verification_status": "verified"}
            )
            if user:
                password = user.get("password")
                print(f"User found for '{email}', password retrieved.")
                return password
            else:
                print(f"User with email '{email}' not found or not verified.")
                return False
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during get user: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred during get user: {e}")
            return False

    def update_user_password(self, email, new_password):
        """
        Updates the password for a user.

        Args:
            email (str): The email of the user whose password needs to be updated.
            new_password (str): The new password (should be hashed in a real application).

        Returns:
            bool: True if the password was updated successfully, False otherwise.
        """
        if not self._check_connection():
            return False
        try:
            # Update the password for the document matching the email
            result = self.users_collection.update_one(
                {"email": email},
                {"$set": {"password": new_password}} # IMPORTANT: In a real application, hash this password!
            )
            if result.matched_count > 0:
                print(f"Password for '{email}' updated successfully!")
                return True
            else:
                print(f"User with email '{email}' not found for password update.")
                return False
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during password update: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred during password update: {e}")
            return False

    def get_user_login(self, email, password):
        """
        Authenticates a user by checking their email, password, and verification status.

        Args:
            email (str): The email address of the user attempting to log in.
            password (str): The password provided by the user.

        Returns:
            list: A list containing a boolean (True for successful login, False for failure)
                  and a string message or the user's email.
        """
        if not self._check_connection():
            return [False, "Database not connected."]
        try:
            # Find a user document that matches email, password, and is verified
            user = self.users_collection.find_one(
                {"email": email, "password": password, "verification_status": "verified"}
            )
            if user:
                print(f"User '{email}' found and verified for login.")
                return [True, user.get("email")] # Return the email as success identifier
            else:
                print(f"User '{email}' not found, password mismatch, or email is not verified.")
                return [False, "User not found, password mismatch, or email is not verified."]
        except OperationFailure as e:
            print(f"❌ MongoDB operation error during login: {e}")
            return [False, str(e)]
        except Exception as e:
            print(f"❌ An unexpected error occurred during login: {e}")
            return [False, str(e)]

# Example Usage:
# To use this class, create a .env file in the same directory as your Python script
# and add your MongoDB Atlas connection string:
#
# .env file content:
# MONGO_URI="mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority"
# MONGO_DB_NAME="your_database_name" # Optional: if your URI doesn't specify a database or you want to override

# if __name__ == "__main__":
#     # Instantiate the Database class
#     db_instance = Database()

#     # --- Example: Create a user ---
#     # print("\n--- Creating a new user ---")
#     # print(db_instance.create_user("john_doe", "john.doe@example.com", "securepass123", "pending"))
#     # # Attempt to create the same user again (should fail)
#     # print(db_instance.create_user("john_doe", "john.doe@example.com", "anotherpass", "pending"))

#     # --- Example: Check verification status ---
#     # print("\n--- Checking verification status ---")
#     # print(db_instance.check_verification_status("john.doe@example.com"))
#     # print(db_instance.check_verification_status("nonexistent@example.com"))

#     # --- Example: Update verification status ---
#     # print("\n--- Updating verification status ---")
#     # print(db_instance.update_verification_status("john.doe@example.com", "verified"))
#     # print(db_instance.check_verification_status("john.doe@example.com"))

#     # --- Example: Get user (password for verified user) ---
#     # print("\n--- Getting user password ---")
#     # password = db_instance.get_user("john.doe@example.com")
#     # if password:
#     #     print(f"Retrieved password for john.doe@example.com: {password}")
#     # else:
#     #     print("Could not retrieve password.")

#     # --- Example: Update user password ---
#     # print("\n--- Updating user password ---")
#     # print(db_instance.update_user_password("john.doe@example.com", "new_secure_password_456"))
#     # password_after_update = db_instance.get_user("john.doe@example.com")
#     # if password_after_update:
#     #     print(f"New password for john.doe@example.com: {password_after_update}")

#     # --- Example: User login ---
#     # print("\n--- Testing user login ---")
#     # # Successful login
#     # print(db_instance.get_user_login("john.doe@example.com", "new_secure_password_456"))
#     # # Incorrect password
#     # print(db_instance.get_user_login("john.doe@example.com", "wrongpass"))
#     # # Non-existent user
#     # print(db_instance.get_user_login("jane.doe@example.com", "anypass"))
#     # # Unverified user (if we had created one and not verified it)
#     # db_instance.create_user("unverified_user", "unverified@example.com", "unverified_pass", "pending")
#     # print(db_instance.get_user_login("unverified@example.com", "unverified_pass"))


#     # Close the connection when done
#     # db_instance.close_connection()
