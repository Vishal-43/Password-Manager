from typing import Union
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi import FastAPI, Request ,Form,HTTPException 
import re

from starlette.middleware.sessions import SessionMiddleware
import databse 
import sendmail 


db = databse.Database()



password_regex = re.compile(r'''^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$''')


def is_strong_password(password: str) -> bool:
    return bool(password_regex.match(password))

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="@tuzi$layki$nahi$bhava@")

templates = Jinja2Templates(directory="templates")


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/",response_class=HTMLResponse)
async def read_root(request:Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request:Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup", response_class=HTMLResponse)
async def post_signup(username : str = Form(...),email : str = Form(...),password : str = Form(...), confirm_password : str = Form(...),request: Request = None):
    print(username, email, password, confirm_password)
    if not is_strong_password(password):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character."})
    elif confirm_password != password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match with Confirm password."})
    else:
        user = db.Sign_up(username=username, email=email, password=password)
        if user:
            return RedirectResponse(url="/login", status_code=303)
        else:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Signup failed."})
    
