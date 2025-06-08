from typing import Union
import re
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

# Assuming the corrected database class is in database.py
from databse import Database
import sendmail

# --- Configuration and Initialization ---

SECRET_KEY = "@tuzi$layki$nahi$bhava@"
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")
STRONG_PASSWORD_MESSAGE = "Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, one number, and one special character."

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
db = Database()

# --- Helper Functions and Dependencies ---

def is_strong_password(password: str) -> bool:
    """Validates the strength of a given password."""
    return bool(PASSWORD_REGEX.match(password))

def get_session_email(request: Request, key: str = "unverified_email") -> str:
    """Dependency to get a required email from the session."""
    email = request.session.get(key)
    if not email:
        # Redirect to signup if the session is invalid or has expired
        raise HTTPException(status_code=HTTP_303_SEE_OTHER, detail="Session expired.", headers={"Location": "/signup"})
    return email

# --- Route Handlers ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def post_signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match."})
    
    if not is_strong_password(password):
        return templates.TemplateResponse("signup.html", {"request": request, "error": STRONG_PASSWORD_MESSAGE})

    # CORRECTED: Removed verification_status argument
    is_success, message = db.create_user(username=username, email=email, password=password)
    
    if not is_success:
        return templates.TemplateResponse("signup.html", {"request": request, "error": message})

    verification_code = sendmail.send_verification_code(email=email)
    request.session['verification_code'] = verification_code
    request.session['unverified_email'] = email
    
    return RedirectResponse(url="/verify", status_code=HTTP_303_SEE_OTHER)

@app.get("/verify", response_class=HTMLResponse)
def get_verification_page(request: Request, email: str = Depends(get_session_email)):
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})

@app.post("/verify")
async def post_verification(
    request: Request,
    code: str = Form(...),
    email: str = Depends(get_session_email)
):
    # CORRECTED: Unpacking was incorrect, now gets single status value
    status = db.check_verification_status(email=email)
    
    if status == "verified":
        return templates.TemplateResponse("verify.html", {"request": request, "message": "Email already verified."})
    
    session_code = request.session.get('verification_code')
    if session_code != code:
        return templates.TemplateResponse("verify.html", {"request": request, "message": "Invalid verification code."})

    # CORRECTED: Changed keyword argument from verification_status to status
    db.update_verification_status(email=email, status="verified")
    request.session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    # CORRECTED: Renamed function to match database.py
    is_valid, user_data_or_error = db.get_user_for_login(email=email, password=password)
    
    if not is_valid:
        return templates.TemplateResponse("login.html", {"request": request, "error": user_data_or_error})
    
    request.session['user'] = user_data_or_error
    return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request):
    if 'user' not in request.session:
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("dashbord.html", {"request": request, "user": request.session['user']})

@app.post("/dashboard", response_class=HTMLResponse)
######################################### in progress #####################################


@app.get("/forgot_passsword", response_class=HTMLResponse)
def get_forgot_password(request: Request):
    return templates.TemplateResponse("forgotpassword.html", {"request": request})

@app.post("/forgot_passsword")
async def post_forgot_password(request: Request, email: str = Form(...)):
    if not db.get_user(email=email):
        return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "Email not found."})
    
    reset_code = sendmail.send_password_reset_code(email=email)
    request.session['reset_code'] = reset_code
    request.session['reset_email'] = email
    return RedirectResponse(url="/reset_password_verify", status_code=HTTP_303_SEE_OTHER)

@app.get("/reset_password_verify", response_class=HTMLResponse)
def get_reset_password_verify(request: Request):
    return templates.TemplateResponse("reset_password_code_verification.html", {"request": request})

@app.post("/reset_password_verify")
async def post_reset_password_verify(
    request: Request,
    reset_code: str = Form(...),
    email: str = Depends(lambda r: get_session_email(r, "reset_email"))
):
    session_code = request.session.get('reset_code')
    if session_code != reset_code:
        return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": "Invalid code."})
    
    return RedirectResponse(url="/reset_password", status_code=HTTP_303_SEE_OTHER)

@app.get("/reset_password", response_class=HTMLResponse)
def get_reset_password(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.post("/reset_password")
async def post_reset_password(
    request: Request,
    new_password: str = Form(...),
   
    
):
    email = request.session.get('reset_email')
    if not email:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Session expired. Please try again."})
    if not is_strong_password(new_password):
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": STRONG_PASSWORD_MESSAGE})

    db.update_user_password(email=email, password=new_password)
    # Clear the specific session keys used for password reset
    request.session.pop('reset_code', None)
    request.session.pop('reset_email', None)
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)
