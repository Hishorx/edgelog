from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("edgelog.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM trades")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trades WHERE result='win'")
    wins = cur.fetchone()[0]

    win_rate = (wins / total * 100) if total > 0 else 0

    # equity curve
    cur.execute("SELECT profit FROM trades ORDER BY id ASC")
    rows = cur.fetchall()

    equity = []
    total_profit = 0

    for r in rows:
        total_profit += float(r["profit"])
        equity.append(total_profit)

    # simple calendar (real dates)
    cur.execute("SELECT date, profit FROM trades")
    data = cur.fetchall()

    calendar = {}

    for d in data:
        day = d["date"]
        calendar[day] = calendar.get(day, 0) + float(d["profit"])

    conn.close()

    return render_template(
        "index.html",
        trades=trades,
        total=total,
        win_rate=round(win_rate, 2),
        equity=equity,
        calendar=calendar
    )

# ---------------- ADD TRADE ----------------
@app.route("/add", methods=["POST"])
def add():
    symbol = request.form["symbol"]
    result = request.form["result"]
    profit = float(request.form["profit"])
    notes = request.form["notes"]
    date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO trades (symbol, result, profit, notes, date)
        VALUES (?,?,?,?,?)
    """, (symbol, result, profit, notes, date))

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
