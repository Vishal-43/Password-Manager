import psycopg2


class Database:
    def start_connnection(self):
        try:
        # Connect to your 'stockly' PostgreSQL database
            conn = psycopg2.connect(
            host="localhost",
            port="5432",  # Default port; change if needed
            database="stockly",
            user="postgres",      # 🔁 Replace this
            password="Vishal#33"   # 🔁 Replace this
                )
                
            print("✅ Connected to PostgreSQL successfully.")
            return conn
        except Exception as e:
            print("❌ Error:", e)
            return None
        # return conn
    def create_user(self,username,email,password,verification_status):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False  # Connection failed
        else:
            try:
                cursor = conn.cursor()

                    # Create atable
                cursor.execute('''
    CREATE TABLE IF NOT EXISTS "USER" (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        verification_status TEXT NOT NULL
    )
''')
                cursor.execute('''
            SELECT 1 FROM "USER" WHERE email = %s
        ''', (email,))

        # If the email already exists, cursor.fetchone() will return a result
                if cursor.fetchone():
                    print("Email is already registered.")
                    self.close_connection(conn)
                    return False
                else:
                    # Insert data into the "USER" table
                    cursor.execute('''
                        INSERT INTO "USER" (username, email, password,verification_status)
                        VALUES (%s, %s, %s, %s)
                    ''', (username, email, password,verification_status))
                    
            # Commit the transaction to save the changes
                    conn.commit()
                    print("User registered successfully!")
                self.close_connection(conn)
                return True

            except Exception as e:
                print("❌ Error:", e)
                self.close_connection(conn)
                return False
       
        
    def close_connection(self,conn):
        cursor = conn.cursor()
        if conn:
            cursor.close()
            conn.close()
            print("🔒 PostgreSQL connection closed.")
          



    def check_verification_status(self,email):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False
        else:
            try:
                cursor = conn.cursor()
                query = 'SELECT verification_status FROM "USER" WHERE email = %s;'

                cursor.execute(query, (email,))
                verification_status = cursor.fetchone()

                if verification_status:
                    print("Verification status:", verification_status[0])
                    return verification_status
                else:
                    return False
            except Exception as e:
                print("❌ Error:", e)
                return False
            finally:
                self.close_connection(conn)
   
    def update_verification_status(self,email,verification_status):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False
        else:
            try:
                cursor = conn.cursor()
                query = 'UPDATE "USER" SET verification_status = %s WHERE email = %s'
                cursor.execute(query, (verification_status, email))
                conn.commit()
                print("Verification status updated successfully!")
            except Exception as e:
                print("❌ Error:", e)
                return False
            finally:
                self.close_connection(conn)
    def get_user(self,email):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False
        else:
            try:
                cursor = conn.cursor()
                query = 'SELECT password FROM "USER" WHERE email = %s AND verification_status = %s'
                cursor.execute(query, (email, "verified"))
                user = cursor.fetchone()
                if user:
                    print("User found:", user[0])
                    return user
                else:
                    print("User not found.")
                    return False
            except Exception as e:
                print("❌ Error:", e)
                return False
            finally:
                self.close_connection(conn)

    def update_user_password(self,email,password):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False
        else:
            try:
                cursor = conn.cursor()
                query = 'UPDATE "USER" SET password = %s WHERE email = %s'
                cursor.execute(query, (password, email))
                conn.commit()
                print("Password updated successfully!")
            except Exception as e:
                print("❌ Error:", e)
                return False
            finally:
                self.close_connection(conn)
    def get_user_login(self,email,password):
        conn = self.start_connnection()
        if conn is None:
            self.close_connection(conn)
            return False
        else:
            try:
                cursor = conn.cursor()
                query = 'SELECT * FROM "USER" WHERE email = %s AND password = %s AND verification_status = %s'
                cursor.execute(query, (email, password,"verified"))
                user = cursor.fetchone()
                if user:
                    print("User found:", user[0])
                    return user
                else:
                    print("User not found.")
                    return False
            except Exception as e:
                print("❌ Error:", e)
                return False
            finally:
                self.close_connection(conn)