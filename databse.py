import psycopg2
from psycopg2 import pool # Import the connection pool module
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Union, Optional, Tuple, Dict, Any
from urllib.parse import urlparse, parse_qs # For parsing DATABASE_URL if needed

# Load environment variables from a .env file
load_dotenv()

class Database:
    """
    Handles all database operations for the application.
    It uses a connection pool for efficiency and manages connections
    and cursors safely using a context manager.
    """
    _connection_pool: Optional[pool.SimpleConnectionPool] = None

    def __init__(self):
        """Initializes the database connection details and the connection pool."""
        if Database._connection_pool is not None:
            print("Database instance already initialized. Reusing existing pool.")
            return

        conn_params: Dict[str, Any] = {}
        try:
            DATABASE_URL = os.environ.get('DATABASE_URL')

            if DATABASE_URL:
                # Parse the DATABASE_URL into a dictionary of connection parameters
                # This is a common way to parse DSNs when psycopg2.connect doesn't directly
                # take individual kwargs, or when building a pool with kwargs.
                # psycopg2.connect() can take the DSN string directly, but the pool needs kwargs.
                parsed_url = urlparse(DATABASE_URL)
                conn_params = {
                    "host": parsed_url.hostname,
                    "port": parsed_url.port or 5432, # Default to 5432 if not specified
                    "database": parsed_url.path[1:] if parsed_url.path else None, # Remove leading '/'
                    "user": parsed_url.username,
                    "password": parsed_url.password,
                    # Add any query parameters as connection options, e.g., sslmode
                    **{k: v[0] for k, v in parse_qs(parsed_url.query).items()}
                }
                # Remove None values
                conn_params = {k: v for k, v in conn_params.items() if v is not None}
                
                # Add SSL mode for Render if not already in URL (Render usually requires SSL)
                if 'sslmode' not in conn_params and 'render' in (conn_params.get('host') or '').lower():
                    conn_params['sslmode'] = 'require'

            else:
                # Fallback for local development if needed, using individual local credentials
                conn_params = {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": int(os.getenv("DB_PORT", "5432")), # Ensure port is int
                    "database": os.getenv("DB_NAME"),
                    "user": os.getenv("DB_USER"),
                    "password": os.getenv("DB_PASSWORD")
                }
                # Filter out None values in case env vars are missing
                conn_params = {k: v for k, v in conn_params.items() if v is not None}

            if not conn_params.get("database"):
                raise ValueError("Database name (DB_NAME or part of DATABASE_URL) is not set.")

            # Initialize the connection pool
            # Min and max connections in the pool
            min_conn = int(os.getenv("DB_MIN_CONN", "1"))
            max_conn = int(os.getenv("DB_MAX_CONN", "10"))
            Database._connection_pool = pool.SimpleConnectionPool(min_conn, max_conn, **conn_params)
            
            print("✅ Database connection pool initialized successfully.")
            
            # Test connection and create tables on startup
            with self.get_connection() as (conn, cursor):
                if conn:
                    print("✅ Database connection established successfully from pool.")
                    self._create_tables() # Call the _create_tables method
                else:
                    raise ConnectionError("Failed to establish database connection from pool.")

        except Exception as e:
            print(f"❌ Critical Error during Database initialization: {e}")
            Database._connection_pool = None # Ensure pool is None on failure
            raise # Re-raise the exception to indicate a critical setup failure

    @contextmanager
    def get_connection(self) -> Tuple[Optional[psycopg2.extensions.connection], Optional[psycopg2.extensions.cursor]]:
        """
        Provides a database connection from the pool.
        This method is a context manager, ensuring that connections are
        returned to the pool safely and automatically.
        """
        if Database._connection_pool is None:
            print("❌ Database pool not initialized. Cannot get connection.")
            yield None, None
            return
            
        conn = None
        try:
            conn = Database._connection_pool.getconn() # Get connection from pool
            cursor = conn.cursor()
            yield conn, cursor
        except psycopg2.Error as e:
            print(f"❌ Database Connection Error: {e}")
            if conn:
                # If an error occurs, return the connection to the pool (it might be broken)
                # or consider closing and discarding it if it's truly unrecoverable.
                # For SimpleConnectionPool, putconn handles this.
                Database._connection_pool.putconn(conn)
            yield None, None
        finally:
            if conn:
                # Return the connection to the pool after use
                # This is crucial for connection pooling to work correctly
                Database._connection_pool.putconn(conn)

    def _create_tables(self):
        """Creates the USER and PASSWORDS tables if they don't exist."""
        with self.get_connection() as (conn, cursor):
            if not conn:
                print("❌ Cannot create tables: No database connection.")
                return
            
            # Create USER table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS "USER" (
                    user_id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    verification_status TEXT NOT NULL 
                );
            ''')
            conn.commit()
            
            # Create PASSWORDS table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    website TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password BYTEA NOT NULL, -- CHANGED TO BYTEA for encrypted password
                    FOREIGN KEY (user_id) REFERENCES "USER"(user_id) ON DELETE CASCADE
                );
            ''')
            conn.commit()
            print("Tables 'USER' and 'passwords' are ready.")

    def create_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
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

    def check_verification_status(self, email: str) -> Optional[str]:
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

    def update_verification_status(self, email: str, status: str = "verified") -> Tuple[bool, str]:
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

    def get_user(self, email: str) -> Optional[Tuple]:
        """
        Retrieves a user by email.
        Returns the user record as a tuple or None if not found.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return None
            
            cursor.execute('SELECT * FROM "USER" WHERE email = %s', (email,))
            return cursor.fetchone()

    def get_user_by_id(self, user_id: int) -> Optional[Tuple]:
        """
        Retrieves a user by ID.
        Returns the user record as a tuple or None if not found.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return None
            
            cursor.execute('SELECT * FROM "USER" WHERE id = %s', (user_id,))
            return cursor.fetchone()

    def update_user_password(self, email: str, password: str) -> Tuple[bool, str]:
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

    def get_user_for_login(self, email: str, password: str) -> Tuple[bool, Union[str, Dict]]:
        """
        Verifies user credentials for login.
        Returns a tuple: (success: bool, data: Union[str, dict])
        On success, data is a dict with user info. On failure, it's an error message.
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."
            
            cursor.execute(
                'SELECT user_id, username, email FROM "USER" WHERE email = %s AND password = %s AND verification_status = %s',
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
    
    def delete_user(self, email: str) -> Tuple[bool, str]:
        """
        Deletes a user by email.
        Returns a tuple: (success: bool, message: str)
        """
        with self.get_connection() as (conn, cursor):
            if not conn:
                return False, "Database connection error."

            cursor.execute('DELETE FROM "USER" WHERE email = %s', (email,))
            conn.commit()
            if cursor.rowcount > 0:
                return True, "User deleted successfully."
            else:
                return False, "User not found."
            
    def save_password(self, user_id: int, website: str, username: str, encrypted_password: bytes) -> Tuple[bool, str]:
        """
        Saves an encrypted password for a specific user.

        Args:
            user_id (int): The ID of the user who owns this password.
            website (str): The name of the website or service.
            username (str): The username for the external service.
            encrypted_password (bytes): The password, ALREADY ENCRYPTED by the application.

        Returns:
            A tuple: (success: bool, message: str)
        """
        sql = """
            INSERT INTO passwords (user_id, website, username, password) 
            VALUES (%s, %s, %s, %s);
        """
        print(f"Saving password: user_id={user_id}, website={website}, username={username}, encrypted_password_len={len(encrypted_password)}") # Debugging line
        
        try:
            with self.get_connection() as (conn, cursor):
                if not conn:
                    return False, "Database connection error."
                cursor.execute(sql, (user_id, website, username, encrypted_password))
                conn.commit()
                return True, "Password saved successfully."
        except psycopg2.Error as e:
            return False, f"Database error: {e}"
        
    def list_passwords(self, user_id: int) -> Tuple[bool, Union[list, str]]:
        """
        Lists all passwords for a specific user.

        Args:
            user_id (int): The ID of the user whose passwords are to be listed.

        Returns:
            A tuple: (success: bool, data: Union[list, str])
            On success, data is a list of dictionaries containing password details.
            On failure, data is an error message.
        """
        sql = "SELECT id, website, username, password FROM passwords WHERE user_id = %s;"

        try:
            with self.get_connection() as (conn, cursor):
                if not conn:
                    return False, "Database connection error."
                cursor.execute(sql, (user_id,))
                rows = cursor.fetchall()
                passwords = [
                    {
                        "id": row[0],
                        "website": row[1],
                        "username": row[2],
                        "encrypted_password": bytes(row[3]) # This will now be bytes from BYTEA column
                    } for row in rows
                ]
                return True, passwords
        except psycopg2.Error as e:
            return False, f"Database error: {e}"

    def delete_password(self, password_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Deletes a password entry from the database.

        Args:
            password_id (int): The ID of the password to delete.
            user_id (int): The ID of the user who owns this password (for security).

        Returns:
            A tuple: (success: bool, message: str)
        """
        sql = "DELETE FROM passwords WHERE id = %s AND user_id = %s;"

        try:
            with self.get_connection() as (conn, cursor):
                if not conn:
                    return False, "Database connection error."
                cursor.execute(sql, (password_id, user_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Password deleted successfully."
                else:
                    return False, "Password not found or you do not have permission to delete it."
        except psycopg2.Error as e:
            return False, f"Database error: {e}"
            
    def update_password(self, password_id: int, user_id: int, encrypted_password: bytes) -> Tuple[bool, str]:
        """
        Updates an encrypted password for a specific password entry.

        Args:
            password_id (int): The ID of the password entry to update.
            user_id (int): The ID of the user who owns this password (for security).
            encrypted_password (bytes): The new encrypted password.

        Returns:
            A tuple: (success: bool, message: str)
        """
        sql = """
            UPDATE passwords SET password = %s WHERE id = %s AND user_id = %s;
        """
        print(f"Updating password ID {password_id} for user {user_id}: encrypted_password_len={len(encrypted_password)}") # Debugging line
        
        try:
            with self.get_connection() as (conn, cursor):
                if not conn:
                    return False, "Database connection error."
                cursor.execute(sql, (encrypted_password, password_id, user_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Password updated successfully."
                else:
                    return False, "Password not found or you do not have permission to update it."
        except psycopg2.Error as e:
            return False, f"Database error: {e}"

# Create a global instance of the Database class
# This will trigger the __init__ and attempt to connect/create tables.
try:
    db = Database() 
    # Example usage after initialization
    # password = db.list_passwords(1)
    # print(password[1] if password[0] else password[1]) # Print data on success, error on 
    db._create_tables()
   
except Exception as e:
    print(f"Application failed to start due to database initialization error: {e}")
    # Handle the error, perhaps exit the application or disable DB-dependent features