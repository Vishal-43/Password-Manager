from typing import Union
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi import FastAPI, Request as FastAPIRequest ,Form,HTTPException # REVIEW: Renamed Request to FastAPIRequest to avoid conflict if Request is used from starlette.requests elsewhere directly
import re

from starlette.middleware.sessions import SessionMiddleware
import databse # REVIEW: Assuming this module handles database operations
import sendmail # REVIEW: Assuming this module handles email sending

# REVIEW: It's good practice to initialize the database connection globally if it's meant to be a singleton.
# If 'Database()' establishes a new connection every time, consider managing connections more explicitly (e.g., dependency injection, or a global instance).
db = databse.Database()


# REVIEW: Regex for password strength is well-defined.
password_regex = re.compile(r'''^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$''')

# Helper function to check password strength
def is_strong_password(password: str) -> bool:
    return bool(password_regex.match(password))

app = FastAPI()
# REVIEW: Good use of SessionMiddleware. Ensure the secret_key is very strong and managed securely in production (e.g., environment variable).
app.add_middleware(SessionMiddleware, secret_key="@tuzi$layki$nahi$bhava@")

templates = Jinja2Templates(directory="templates")

# Optional: mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/",response_class=HTMLResponse)
def read_root(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup",response_class=HTMLResponse)
def signup(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup",response_class=HTMLResponse)
async def post_signup(username : str = Form(...),
                      email : str = Form(...),
                      password : str = Form(...), 
                      confirm_password : str = Form(...),
                      request: FastAPIRequest = None): # REVIEW: Changed Request to FastAPIRequest. Defaulting to None for injected dependency is unusual; FastAPI injects it if type-hinted.
    
    if password != confirm_password:
        error_message = "Passwords do not match"
        return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
    # REVIEW: Using the is_strong_password helper function here for a comprehensive check.
    # The previous `len(password) < 8` was only a partial check, while the error message implied all criteria.
    elif not is_strong_password(password):
        error_message = "Password is not strong enough. It should have at least: 8 characters, one uppercase letter, one lowercase letter, one number, and one special character."
        return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
    
    else:
        # REVIEW: Consider adding try-except blocks around database and email operations for more robust error handling.
        # For example, if db.create_user or sendmail.send_verification_code raises an unexpected error.
        try:
            res = db.create_user(username=username,email=email,password=password,verification_status="not_verified")
            # REVIEW: Debug print statements. Consider using a proper logging framework for production.
            # print("res",res)
            # print("success ✅")
            if res[0]: # Assuming res is (bool_success, message_or_data)
                
                success_message = "User created successfully! Please check your email to verify your account." # REVIEW: Slightly more informative success message.
                verification_code = sendmail.send_verification_code(email=email)
                request.session['verification_code'] = verification_code
                request.session['unverified_email'] = email
                # print("sucess ✅") # REVIEW: Debug print
                # REVIEW: It's good practice to show a message on the verify page itself, or on the signup page after redirect.
                # A redirect to /verify is good. The message can be passed via flash messages if your template engine supports it, or handled on the /verify page.
                return RedirectResponse(url="/verify", status_code=303)
            else:
                error_message = res[1] # Assuming res[1] is the error message from db
                return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
        except Exception as e:
            # REVIEW: Basic exception handling. Log the error for debugging.
            # In a production app, you might want a more sophisticated error logging/reporting mechanism.
            # print(f"An error occurred during signup: {e}") # For debugging
            error_message = "An unexpected error occurred. Please try again later."
            return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})

@app.get("/verify", response_class=HTMLResponse)
async def get_verification_page(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    email = request.session.get('unverified_email')
    if not email:
        # REVIEW: Redirecting to signup if no email is in session is a good fallback.
        return RedirectResponse(url="/signup", status_code=303)
    
    # REVIEW: Check if already verified before showing the form, could be a small UX improvement.
    # status_check = db.check_verification_status(email=email)
    # if status_check[0] == "verified":
    #     # User is already verified, maybe redirect to login or show a message.
    #     # For now, letting it proceed to the verification page as per original logic.
    #     pass

    return templates.TemplateResponse("verify.html", {"request": request, "message": "Please enter the verification code sent to your email."})

@app.post("/verify", response_class=HTMLResponse)
async def post_verification_code(request: FastAPIRequest, code: str = Form(...)): # REVIEW: Changed Request to FastAPIRequest
    email = request.session.get('unverified_email')
    stored_verification_code = request.session.get('verification_code')

    if not email or not stored_verification_code: # REVIEW: Also check if stored_verification_code exists
        # REVIEW: If email or code is not in session, perhaps the session expired or was tampered with.
        return RedirectResponse(url="/signup", status_code=303) # Or /login, depending on desired flow.
    
    # REVIEW: Consider adding try-except for db operations
    try:
        status_result = db.check_verification_status(email=email)
        # print("status", status_result) # REVIEW: Debug print

        if status_result[0] == "verified":
            # REVIEW: If already verified, clear session variables related to verification and redirect.
            request.session.pop('verification_code', None)
            request.session.pop('unverified_email', None)
            return templates.TemplateResponse("verify.html", {"request": request, "message": "Email already verified. You can now log in.", "already_verified": True}) # Added a flag for template
        elif status_result[0] == "not_verified":
            # print("sending 💌") # REVIEW: Debug print
            if stored_verification_code == code:
                db.update_verification_status(email=email, verification_status="verified")
                request.session.pop('verification_code', None)
                request.session.pop('unverified_email', None)
                # REVIEW: Redirect to login is appropriate after successful verification.
                # Optionally, could auto-login the user here if desired.
                return RedirectResponse(url="/login?verified=true", status_code=303) # Added a query param for success message on login page
            else:
                return templates.TemplateResponse("verify.html", {"request": request, "message": "Invalid verification code. Please try again."})
        else:
            # This case implies an issue with db.check_verification_status or an unexpected status string
            # print(f"Unexpected verification status: {status_result}") # REVIEW: Debug print
            return templates.TemplateResponse("verify.html", {"request": request, "message": f"Error verifying email. Please try again or contact support."}) 
    except Exception as e:
        # print(f"An error occurred during verification: {e}") # REVIEW: Debug print
        error_message = "An unexpected error occurred during verification. Please try again later."
        return templates.TemplateResponse("verify.html", {"request": request, "message": error_message})

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    # REVIEW: Optionally, display a success message if redirected from verification.
    verified_message = "Account successfully verified. Please log in." if request.query_params.get("verified") else None
    return templates.TemplateResponse("login.html", {"request": request, "success_message": verified_message})

@app.post("/login", response_class=HTMLResponse)
async def post_login(request: FastAPIRequest, email: str = Form(...), password: str = Form(...)): # REVIEW: Changed Request to FastAPIRequest
    # REVIEW: Consider try-except for db operations
    try:
        user_data = db.get_user_login(email=email, password=password) # Assuming this hashes and compares password
        # print(request.session.get('email')) # REVIEW: Debug print, this would be from a previous session if any.
        if user_data[0]: # Assuming user_data is (bool_success, user_details_or_error_message)
            # REVIEW: Ensure verification status is checked before login, or handle it in get_user_login.
            # If login is allowed for unverified users, the application flow should account for that.
            # For example: status = db.check_verification_status(email=email)
            # if status[0] != "verified":
            #    return templates.TemplateResponse("login.html", {"request": request, "error": "Please verify your email before logging in."})
            
            request.session['user'] = user_data[1] # Store relevant, non-sensitive user info.
            request.session['email'] = email # Storing email in session is fine.
            
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            error_message = user_data[1]
            return templates.TemplateResponse("login.html", {"request": request, "error": error_message})
    except Exception as e:
        # print(f"An error occurred during login: {e}") # REVIEW: Debug print
        error_message = "An unexpected error occurred during login. Please try again later."
        return templates.TemplateResponse("login.html", {"request": request, "error": error_message})

@app.get("/forgot_password", response_class=HTMLResponse) # REVIEW: Consistent endpoint naming: /forgot-password
async def get_forgot_password(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    return templates.TemplateResponse("forgotpassword.html", {"request": request})

@app.post("/forgot_password", response_class=HTMLResponse) # REVIEW: Consistent endpoint naming: /forgot-password
async def post_forgot_password(request: FastAPIRequest, email: str = Form(...)): # REVIEW: Changed Request to FastAPIRequest
    # REVIEW: Consider try-except for db and email operations
    try:
        user = db.get_user(email=email) # Assuming this just checks existence by email
        if user: # Assuming user is truthy if found
            verification_code = sendmail.send_password_reset_code(email=email)
            request.session['reset_verification_code'] = verification_code # REVIEW: Using a distinct session key
            request.session['reset_temp_email'] = email # REVIEW: Using a distinct session key
            # REVIEW: Redirect to a page where the user enters the code.
            return RedirectResponse(url="/reset-password-verify-code", status_code=303) # REVIEW: Consistent naming
        else: 
            return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "If an account with that email exists, a password reset code has been sent."}) # REVIEW: More secure message (prevents email enumeration)
    except Exception as e:
        # print(f"An error occurred during forgot password: {e}") # REVIEW: Debug print
        # REVIEW: Even on error, show a generic message to prevent info leaks.
        return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "If an account with that email exists, a password reset code has been sent."})

@app.get("/reset_password_code_verification", response_class=HTMLResponse) # REVIEW: Consistent endpoint naming: /reset-password-verify-code
async def get_reset_password_code_verification(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    email = request.session.get('reset_temp_email') # REVIEW: Using distinct session key
    if not email:
        return RedirectResponse(url="/forgot_password", status_code=303) # REVIEW: Consistent endpoint naming
    return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": ""})
    
@app.post("/reset_password_code_verification", response_class=HTMLResponse) # REVIEW: Consistent endpoint naming: /reset-password-verify-code
async def post_reset_password_code_verification(request: FastAPIRequest, reset_code: str = Form(...)): # REVIEW: Changed Request to FastAPIRequest
    email = request.session.get('reset_temp_email') # REVIEW: Using distinct session key
    verification_code_from_session = request.session.get('reset_verification_code') # REVIEW: Using distinct session key

    if not email or not verification_code_from_session:
        # Session data missing, redirect to start of flow
        return RedirectResponse(url="/forgot_password", status_code=303) # REVIEW: Consistent endpoint naming

    if verification_code_from_session == reset_code:
        # Code is correct, allow password reset. Store a flag or the email securely for the next step.
        request.session['password_reset_email_verified'] = email # This email is now authorized for password reset
        # REVIEW: Clear the reset code now that it's used.
        request.session.pop('reset_verification_code', None)
        return RedirectResponse(url="/reset_password", status_code=303) # REVIEW: Consistent endpoint naming
    else:
        return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": "Invalid verification code."})

@app.get("/reset_password",response_class=HTMLResponse)
async def get_reset_password(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    # REVIEW: Check against 'password_reset_email_verified' instead of 'reset_temp_email' for tighter security.
    # This ensures the user came through the code verification step.
    email_for_reset = request.session.get('password_reset_email_verified') 
    if not email_for_reset:
        # If no email is marked as verified for reset, or 'reset_temp_email' is missing after code verification,
        # redirect to the beginning of the forgot password flow.
        return RedirectResponse(url="/forgot_password", status_code=303) # REVIEW: Consistent endpoint naming
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.post("/reset_password", response_class=HTMLResponse)
async def post_reset_password(request: FastAPIRequest, new_password: str = Form(...), confirm_new_password: str = Form(...)): # REVIEW: Added confirm_new_password
    email_for_reset = request.session.get('password_reset_email_verified') # REVIEW: Check against this key
    
    if not email_for_reset:
        return RedirectResponse(url="/forgot_password", status_code=303) # REVIEW: Consistent endpoint naming
    
    if new_password != confirm_new_password: # REVIEW: Added confirmation check
        error_message = "New passwords do not match."
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": error_message, "email": email_for_reset})

    # REVIEW: Using the is_strong_password helper function here.
    elif not is_strong_password(new_password):
        error_message = "New password is not strong enough. It should have at least: 8 characters, one uppercase letter, one lowercase letter, one number, and one special character."
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": error_message, "email": email_for_reset})
    else:
        # REVIEW: Consider try-except for db operations
        try:
            db.update_user_password(email=email_for_reset, password=new_password) # Assuming this hashes the new password
            # REVIEW: Clear all related session variables after successful password reset.
            request.session.pop('reset_verification_code', None) # Should already be popped, but good to ensure
            request.session.pop('reset_temp_email', None)
            request.session.pop('password_reset_email_verified', None)
            # REVIEW: Redirect to login with a success message.
            return RedirectResponse(url="/login?reset=success", status_code=303) # Pass a query param for message
        except Exception as e:
            # print(f"An error occurred during password reset: {e}") # REVIEW: Debug print
            error_message = "An unexpected error occurred while resetting your password. Please try again."
            return templates.TemplateResponse("reset_password.html", {"request": request, "error": error_message, "email": email_for_reset})

# REVIEW: Add a dashboard route for redirection after login.
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    user_email = request.session.get('email')
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)
    
    # user_details = request.session.get('user') # If you stored more user details
    return templates.TemplateResponse("dashboard.html", {"request": request, "email": user_email})

# REVIEW: Add a logout route
@app.get("/logout", response_class=HTMLResponse)
async def logout(request: FastAPIRequest): # REVIEW: Changed Request to FastAPIRequest
    request.session.clear() # Clear the whole session
    return RedirectResponse(url="/login?logged_out=true", status_code=303)

# REVIEW: It's good practice to include this for running with uvicorn directly for development.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

