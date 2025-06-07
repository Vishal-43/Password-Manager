import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

load_dotenv()

import os
from supabase import create_client

url= os.environ.get("SUPABASE_URL")
key= os.environ.get("SUPABASE_KEY")
supabase= create_client(url, key)

class Database:
    def Sign_up(self, username, email, password):
        try:
            
            user_auth_response = supabase.auth.sign_up({"email": email, "password": password})
            
            
            if user_auth_response and user_auth_response.user:
                print(f"User '{email}' successfully signed up with Supabase authentication.")
                
                
                try:
                    data = supabase.table("users").insert({"username": username, "email": email,"password":password}).execute() 
                    print(f"User details inserted into 'users' table for '{username}'.")
                    return user_auth_response.user #
                except Exception as db_e:
                    print(f"Error inserting user details into 'users' table after successful auth: {db_e}")
                   
                    return None # Indicate failure in database insertion
            else:
              
                print(f"Supabase authentication sign-up did not return a user for {email}.")
                return None

        except Exception as e:
            # Catch all other exceptions, including Supabase auth errors
            print(f"Error signing up: {e}")
            
            # You can add more specific error handling based on the exception type or message from Supabase.
            # For example, checking for specific error codes or messages.
            if "User already registered" in str(e): # Example of checking error message
                print("Hint: This email address is already registered.")
            elif "Password should be at least 6 characters" in str(e):
                print("Hint: Password must be at least 6 characters long.")
            
            return None


    def log_in(self, email, password):
        try:
            user = supabase.auth.sign_in({ "email": email, "password": password })
            return user
        except Exception as e:
            print("Error logging in:", e)
            return None