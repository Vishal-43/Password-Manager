import psycopg2
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables from a .env file
load_dotenv()

class Database:
    """
    Handles all database operations for the application.
    It uses a connection pool for efficiency and manages connections
    and cursors safely using a context manager.
    """
    def __init__(self):
        """Initializes the database connection details."""
        try:
            self.conn_params = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": os.getenv("DB_PORT", "5432"),
                "database": os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD")
            }
            # Test connection on startup
            with self.get_connection() as conn:
                if conn:
                    print("✅ Database connection established successfully.")
                    self._create_user_table()
                else:
                    raise ConnectionError("Failed to establish database connection.")
        except Exception as e:
            print(f"❌ Critical Error during Database initialization: {e}")
            self.conn_params = None

    @contextmanager
    def get_connection(self):
        """
        Provides a database connection from the pool.
        This method is a context manager, ensuring that connections are
        returned to the pool safely and automatically.
        """
        if not self.conn_params:
            yield None, None
            return
            
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()
            yield conn, cursor
        except psycopg2.Error as e:
            print(f"❌ Database Connection Error: {e}")
            yield None, None
        finally:
            if conn:
                conn.close()

    def _create_user_table(self):
        """Creates the USER table if it doesn't exist."""
        with self.get_connection() as (conn, cursor):
            if not conn:
                return
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS "USER" (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    verification_status TEXT NOT NULL 
                );
            ''')
            conn.commit()
            print("Table 'USER' is ready.")

    def create_user(self, username, email, password):
        """
        Creates a new user in the database.
        Returns a tuple: (success: bool, message: str)
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."

            try:
                # Check if email already exists
                cursor.execute('SELECT email FROM "USER" WHERE email = %s', (email,))
                if cursor.fetchone():
                    return False, "Email is already registered."

                # Insert new user
                cursor.execute(
                    'INSERT INTO "USER" (username, email, password, verification_status) VALUES (%s, %s, %s, %s)',
                    (username, email, password, "not_verified")
                )
                conn.commit()
                return True, "User created successfully."
            except psycopg2.Error as e:
                return False, str(e)

    def check_verification_status(self, email):
        """
        Checks the verification status for a given email.
        Returns the status string ("verified" or "not_verified") or None if not found.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return None

            cursor.execute('SELECT verification_status FROM "USER" WHERE email = %s', (email,))
            result = cursor.fetchone()
            return result[0] if result else None

    def update_verification_status(self, email, status="verified"):
        """
        Updates the user's verification status.
        Returns a tuple: (success: bool, message: str)
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."
            
            cursor.execute('UPDATE "USER" SET verification_status = %s WHERE email = %s', (status, email))
            conn.commit()
            # rowcount checks if any row was updated
            if cursor.rowcount > 0:
                return True, "Verification status updated."
            else:
                return False, "User not found."

    def get_user(self, email):
        """
        Retrieves a user by email.
        Returns the user record as a tuple or None if not found.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return None
            
            cursor.execute('SELECT * FROM "USER" WHERE email = %s', (email,))
            return cursor.fetchone()

    def update_user_password(self, email, password):
        """
        Updates a user's password.
        Returns a tuple: (success: bool, message: str)
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."

            cursor.execute('UPDATE "USER" SET password = %s WHERE email = %s', (password, email))
            conn.commit()
            if cursor.rowcount > 0:
                return True, "Password updated successfully."
            else:
                return False, "User not found."

    def get_user_for_login(self, email, password):
        """
        Verifies user credentials for login.
        Returns a tuple: (success: bool, data: Union[str, dict])
        On success, data is a dict with user info. On failure, it's an error message.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."
            
            cursor.execute(
                'SELECT id, username, email FROM "USER" WHERE email = %s AND password = %s AND verification_status = %s',
                (email, password, "verified")
            )
            user = cursor.fetchone()

            if user:
                user_data = {"id": user[0], "username": user[1], "email": user[2]}
                return True, user_data
            else:
                # Check if the user exists but credentials are wrong or not verified
                cursor.execute('SELECT verification_status FROM "USER" WHERE email = %s', (email,))
                result = cursor.fetchone()
                if not result:
                    return False, "Invalid email or password."
                if result[0] == 'not_verified':
                    return False, "Account not verified. Please check your email."
                return False, "Invalid email or password."

 
