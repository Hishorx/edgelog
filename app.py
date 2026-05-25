from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.secret_key = "edgelog_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")

# Fix postgres:// issue
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    symbol = db.Column(db.String(50))
    result = db.Column(db.String(20))
    profit = db.Column(db.Float)
    notes = db.Column(db.String(500))
    date = db.Column(db.String(50))

# ---------------- CREATE TABLES ----------------
with app.app_context():
    db.create_all()

# ---------------- HOME ----------------
@app.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")

    trades = Trade.query.filter_by(user_id=session["user_id"])\
        .order_by(Trade.id.desc()).all()

    total = len(trades)

    wins = len([t for t in trades if t.result == "win"])

    win_rate = (wins / total * 100) if total > 0 else 0

    equity = []
    running = 0

    for t in reversed(trades):
        running += t.profit
        equity.append(running)

    calendar = {}

    for t in trades:
        if t.date not in calendar:
            calendar[t.date] = 0
        calendar[t.date] += t.profit

    return render_template(
        "index.html",
        trades=trades,
        total=total,
        win_rate=round(win_rate, 2),
        equity=equity,
        calendar=calendar
    )

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        existing = User.query.filter_by(username=username).first()

        if existing:
            return "User already exists"

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect("/")

        return "Invalid credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ADD TRADE ----------------
@app.route("/add", methods=["POST"])
def add_trade():

    if "user_id" not in session:
        return redirect("/login")

    trade = Trade(
        user_id=session["user_id"],
        symbol=request.form["symbol"],
        result=request.form["result"],
        profit=float(request.form["profit"]),
        notes=request.form["notes"],
        date=datetime.now().strftime("%Y-%m-%d")
    )

    db.session.add(trade)
    db.session.commit()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
