from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "edgelog_secret_key"

# ---------------- DB ----------------
def db():
    conn = sqlite3.connect("edgelog.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()

    # users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # trades table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            result TEXT,
            profit REAL,
            notes TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM trades WHERE user_id=? ORDER BY id DESC", (session["user_id"],))
    trades = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM trades WHERE user_id=?", (session["user_id"],))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trades WHERE user_id=? AND result='win'", (session["user_id"],))
    wins = cur.fetchone()[0]

    win_rate = (wins / total * 100) if total > 0 else 0

    conn.close()

    return render_template("index.html",
                           trades=trades,
                           total=total,
                           win_rate=round(win_rate, 2))

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = db()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?,?)",
                        (username, password))
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ADD TRADE ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    symbol = request.form["symbol"]
    result = request.form["result"]
    profit = float(request.form["profit"])
    notes = request.form["notes"]

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO trades (user_id, symbol, result, profit, notes, date)
        VALUES (?,?,?,?,?,date('now'))
    """, (session["user_id"], symbol, result, profit, notes))

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
