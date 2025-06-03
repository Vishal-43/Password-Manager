from typing import Union
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi import FastAPI,Request ,Form,HTTPException
import re

from starlette.middleware.sessions import SessionMiddleware
import databse
import sendmail
db = databse.Database()


password_regex = re.compile(r'''^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$''')

# Helper function to check password strength
def is_strong_password(password: str) -> bool:
    return bool(password_regex.match(password))



app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="@tuzi$layki$nahi$bhava@")  # Use a strong secret in production

templates = Jinja2Templates(directory="templates")

# Optional: mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/",response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup",response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup",response_class=HTMLResponse)
async def post_signup(username : str = Form(...),
                      email : str = Form(...),
                       password : str = Form(...), 
                       confirm_password : str = Form(...),
                       request: Request = None):
    
    if password != confirm_password:
        error_message = "Passwords do not match"
        return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
    elif len(password) < 8:
        error_message = "Password is not strong enough. It should have at least: 8 characters, one uppercase letter, one lowercase letter, one number, and one special character."
        return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
    
    else:
        
        res = db.create_user(username=username,email=email,password=password,verification_status="not_verified")
        if res:
            
            success_message = "User created successfully!"
            verification_code = sendmail.send_verification_code(email=email)
            request.session['verification_code'] = verification_code  # Store verification code in session
            request.session['unverified_email'] = email  # Store email in session
            return RedirectResponse(url="/verify", status_code=303)
            # return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
            # return templates.TemplateResponse("signup.html", {"request": request, "success": success_message})

        else:
            error_message = "Error creating user. Please try again."
            return templates.TemplateResponse("signup.html", {"request": request, "error": error_message})
    # return templates.TemplateResponse("signup.html", {"request": request})
@app.get("/verify", response_class=HTMLResponse)
async def get_verification_page(request: Request):
    email = request.session.get('unverified_email')
    if not email:
        return RedirectResponse(url="/signup", status_code=303)
    else:
        return templates.TemplateResponse("verify.html", {"request": request, "message": ""})

@app.post("/verify", response_class=HTMLResponse)
async def post_verification_code(request: Request, code: str = Form(...)):
    email = request.session.get('unverified_email')
    if not email:
        return RedirectResponse(url="/signup", status_code=303)
    else:
        status = db.check_verification_status(email=email)
        print("status",status)
        if status[0] == "verified":
            return templates.TemplateResponse("verify.html", {"request": request, "message": "Email already verified."})
        elif status[0] == "not_verified":
            print("sending 💌")
            verification_code = request.session.get('verification_code')

            if verification_code == code:
                db.update_verification_status(email=email,verification_status="verified")
                request.session.pop('verification_code', None)
                request.session.pop('unverified_email', None)
                return RedirectResponse(url="/login", status_code=303)
            else:
                return templates.TemplateResponse("verify.html", {"request": request, "message": "Invalid verification code."})
        else:
            return templates.TemplateResponse("verify.html", {"request": request, "message": f"Error verifying email."}) 
            

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.get_user_login(email=email, password=password)
    if user:
        request.session['user'] = user[0]
        request.session['email'] = email
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        error_message = "Invalid email or password or email is not verified."
        return templates.TemplateResponse("login.html", {"request": request, "error": error_message})
@app.get("/forgot_passsword", response_class=HTMLResponse)
async def get_forgot_password(request: Request):
    return templates.TemplateResponse("forgotpassword.html", {"request": request})

@app.post("/forgot_passsword", response_class=HTMLResponse)
async def post_forgot_password(request: Request, email: str = Form(...)):
    user = db.get_user(email=email)
    if user:
        verification_code = sendmail.send_password_reset_code(email=email)
        request.session['verification_code'] = verification_code
        request.session['temp_email'] = email
        return RedirectResponse(url="/reset_password_code_verification", status_code=303)
    else: 
        return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "Email not found."})
    # return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "Password reset code sent to your email."})    

@app.get("/reset_password_code_verification", response_class=HTMLResponse)
async def get_reset_password_code_verification(request: Request):
    email = request.session.get('temp_email')
    if not email:
        return RedirectResponse(url="/forgot_passsword", status_code=303)
    else:
        return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": ""})
    
@app.post("/reset_password_code_verification", response_class=HTMLResponse)
async def post_reset_password_code_verification(request: Request, reset_code: str = Form(...)):
    email = request.session.get('temp_email')
    if not email:
        return RedirectResponse(url="/forgot_passsword", status_code=303)
    else:
        verification_code = request.session.get('verification_code')
        if verification_code == reset_code:
            return RedirectResponse(url="/reset_password", status_code=303)
        else:
            return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": "Invalid verification code."})
@app.get("/reset_password",response_class=HTMLResponse)
async def get_reset_password(request: Request):
    email = request.session.get('temp_email')
    if not email:
        return RedirectResponse(url="/forgot_passsword", status_code=303)
    else:
        return templates.TemplateResponse("reset_password.html", {"request": request})

@app.post("/reset_password", response_class=HTMLResponse)
async def post_reset_password(request: Request, new_password: str = Form(...)):
    email = request.session.get('temp_email')
    if not email:
        return RedirectResponse(url="/forgot_passsword", status_code=303)
    else:
        
        if len(new_password) < 8:
            error_message = "Password is not strong enough. It should have at least: 8 characters, one uppercase letter, one lowercase letter, one number, and one special character."
            return templates.TemplateResponse("reset_password.html", {"request": request, "error": error_message})
        else:
            db.update_user_password(email=email,password=new_password)
            request.session.pop('verification_code', None)
            request.session.pop('temp_email', None)
            return RedirectResponse(url="/login", status_code=303)
