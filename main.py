import os
import shutil

from fastapi import FastAPI
from fastapi import Request
from fastapi import Form
from fastapi import UploadFile
from fastapi import File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database import SessionLocal
from database import engine
from database import Base

from models import User
from models import Message

from passlib.context import CryptContext

from starlette.middleware.sessions import SessionMiddleware


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")


if not os.path.exists("uploads"):
    os.makedirs("uploads")


# CURRENT_USER_ID = None

pwd_context = CryptContext( schemes=["bcrypt"],deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return RedirectResponse(url="/login")


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...)
):
    db: Session = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if user:
        return RedirectResponse(url="/register", status_code=303)

    new_user = User(
        username=username,
        password=pwd_context.hash(password)
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db: Session = SessionLocal()

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not pwd_context.verify(password, user.password):
        return RedirectResponse(url="/login", status_code=303)

    request.session["user.id"] = user.id

    return RedirectResponse(url="/chat", status_code=303)


@app.get("/chat")
def chat_page(request: Request):
    CURRENT_USER_ID = request.session.get("user_id")

    if not CURRENT_USER_ID:
        return RedirectResponse(url="/login")

    db: Session = SessionLocal()

    current_user = db.query(User).filter(
        User.id == CURRENT_USER_ID
    ).first()

    users = db.query(User).filter(
        User.id != CURRENT_USER_ID
    ).all()

    dialogs = []

    for user in users:
        count = db.query(Message).filter(
            ((Message.sender_id == CURRENT_USER_ID) &
             (Message.receiver_id == user.id)) |
            ((Message.sender_id == user.id) &
             (Message.receiver_id == CURRENT_USER_ID))
        ).count()

        if count > 0:
            dialogs.append(user)

    selected_user_id = request.query_params.get("user_id")

    selected_user = None
    messages = []

    if selected_user_id:
        selected_user = db.query(User).filter(
            User.id == int(selected_user_id)
        ).first()

        messages = db.query(Message).filter(
            ((Message.sender_id == CURRENT_USER_ID) &
             (Message.receiver_id == int(selected_user_id))) |
            ((Message.sender_id == int(selected_user_id)) &
             (Message.receiver_id == CURRENT_USER_ID))
        ).all()

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "users": users,
            "dialogs": dialogs,
            "messages": messages,
            "selected_user": selected_user,
            "current_user": current_user
        }
    )


@app.post("/send_message")
def send_message(
    request: Request,
    receiver_id: int = Form(...),
    text: str = Form(""),
    file: UploadFile = File(None)
):
    CURRENT_USER_ID = request.session.get("user_id")
    
    if not CURRENT_USER_ID:
        return RedirectResponse(url="/login", status_code=303)

    db: Session = SessionLocal()

    file_name = None
    file_type = None

    if file and file.filename:
        file_name = file.filename
        file_type = file.content_type

        file_path = f"uploads/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    if not text.strip() and (not file or not file.filename):
        return RedirectResponse(url=f"/chat?user_id={receiver_id}",status_code=303)

    message = Message(
        sender_id=CURRENT_USER_ID,
        receiver_id=receiver_id,
        text=text,
        file_name=file_name,
        file_type=file_type
    )

    db.add(message)
    db.commit()

    return RedirectResponse(
        url=f"/chat?user_id={receiver_id}",
        status_code=303
    )
    
@app.get("/logout")
def logout(request: Request):
    
    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303
    )