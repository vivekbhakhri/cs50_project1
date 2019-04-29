import os

from flask import Flask, session, render_template, request, abort, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helper import *


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure app's secret key for cookie signing
app.secret_key = os.urandom(24)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up databases
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

#FOR user to register
@app.route("/signup")
def signup():
    return render_template("register.html")

@app.route("/register", methods={"POST"})
def register():
    username= request.form.get("username")
    email= request.form.get("email")
    password= request.form.get("password")
    error = None
    if not username or not password:
        return render_template("error.html", message="Please enter both username and password")
    hashP= hash_password(password)
    if db.execute("SELECT ID FROM USERDATABASE WHERE username=:username", {"username":username}).fetchone() is not None:
        error = 'User {} is already registered.'.format(username)
        return render_template("error.html", message=error)

    if error is None:
        db.execute("INSERT INTO userdatabase (username, email, password) VALUES (:username, :email, :password)",
        {"username": username, "email": email, "password": hashP})
        db.commit()
    return render_template("success.html", username=username)

#For user to login
@app.route("/for_login")
def for_login():
    return render_template("login.html")

@app.route("/login", methods={"POST"})
def login():
    if request.method=="POST":
        username= request.form.get("username")
        password= request.form.get("password")
        error = None
        if not password:
            return render_template("error.html",message="Please Enter Password")

        user=db.execute("SELECT * FROM USERDATABASE WHERE (email=:username OR username=:username)",{"username":username}).fetchone()
        if user is None:
            error = 'Incorrect username.'
            return render_template("error.html", message=error)
        elif not check_password(user['password'], password):
            error = 'Incorrect password.'
            return render_template("error.html", message=error)
        if error is None:
            session.clear()
            session["logged_in"] = True
            session['user_id'] = user['id']
            return redirect('/home')
        else:
            return redirect("/for_login")


@app.route("/logout")
def logout():
    session["logged_in"] = False
    return render_template("index.html")


# HOME PAGE
@app.route("/home")
def home():
    return render_template("home.html")
# Presenting results
@app.route("/results", methods={"POST"})
def results():
    search = request.form.get("search")
    search = "%" + search + "%"
    rows= db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search OR year LIKE :search", {"search":search})
    if rows.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")
    books=rows.fetchall()
    return render_template('search.html', books=books)
