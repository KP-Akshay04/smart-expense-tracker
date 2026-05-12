from urllib import response

from flask import Flask, render_template, request, redirect, session
from flask import Flask, render_template, request, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import date

app = Flask(__name__)
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
app.secret_key = "supersecretkey" 
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 🔐 required for sessions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # expenses table with user_id ✅
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            amount REAL,
            category TEXT,
            date TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]   # ✅ FIXED
            return redirect('/dashboard')
        else:
            return "Invalid credentials"

    return render_template("login.html")


# 📝 REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            conn.close()
            return "User already exists"

    conn.close()
    return render_template("register.html")


# 🔒 LOGOUT
@app.route('/logout')
def logout():
    session.clear()

    response = redirect('/login')

    response.set_cookie('session', '', expires=0)

    return response


# 🏠 HOME
@app.route('/')
def home():
    return render_template("home.html")


# 📊 DASHBOARD
@app.route('/dashboard')
def index():
    print(session)
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    selected_date = request.args.get('date')

    if selected_date:
        c.execute("""
    SELECT id, title, amount, category, date 
    FROM expenses 
    WHERE user_id=? AND date=?
""", (user_id, selected_date))
    else:
        c.execute("""
    SELECT id, title, amount, category, date 
    FROM expenses 
    WHERE user_id=?
""", (user_id,))

    data = c.fetchall()

    # Stats
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?", (user_id,))
    total = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM expenses WHERE user_id=?", (user_id,))
    count = c.fetchone()[0]

    c.execute("SELECT MAX(amount) FROM expenses WHERE user_id=?", (user_id,))
    max_expense = c.fetchone()[0] or 0

    c.execute("""
        SELECT category, COUNT(*) 
        FROM expenses 
        WHERE user_id=? 
        GROUP BY category 
        ORDER BY COUNT(*) DESC 
        LIMIT 1
    """, (user_id,))
    top = c.fetchone()
    top_category = top[0] if top else "N/A"

    if selected_date:
        c.execute("""
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE user_id=? AND date=? 
        GROUP BY category
    """, (user_id, selected_date))
    else:
        c.execute("""
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE user_id=? 
        GROUP BY category
    """, (user_id,))
    chart_data = c.fetchall()

    conn.close()

    labels = [row[0] for row in chart_data]
    values = [row[1] for row in chart_data]

    response = make_response(render_template("index.html",
                           expenses=data,
                           total=total,
                           count=count,
                           max_expense=max_expense,
                           top_category=top_category,
                           labels=labels,
                           values=values))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# ➕ ADD EXPENSE
@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        today = date.today().isoformat()
        user_id = session['user_id']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO expenses (user_id, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, amount, category, today)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template("add.html")


# ❌ DELETE
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_id = session['user_id']
    c.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ✏️ EDIT
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']

        c.execute("""
            UPDATE expenses 
            SET title=?, amount=?, category=? 
            WHERE id=? AND user_id=?
        """, (title, amount, category, id, user_id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    c.execute("SELECT * FROM expenses WHERE id=? AND user_id=?", (id, user_id))
    expense = c.fetchone()
    conn.close()

    return render_template("edit.html", expense=expense)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)