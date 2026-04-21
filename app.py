from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date   # ✅ NEW

app = Flask(__name__)

# Initialize DB
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            amount REAL,
            category TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "123":
            return redirect('/dashboard')
        else:
            return "Invalid credentials"

    return render_template("login.html")

# Home
@app.route('/')
def home():
    return render_template("login.html")

# Dashboard
@app.route('/dashboard')
def index():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔥 FETCH ALL DATA (MISSING BEFORE)
    c.execute("SELECT * FROM expenses")
    data = c.fetchall()

    # Total expense
    c.execute("SELECT SUM(amount) FROM expenses")
    total = c.fetchone()[0] or 0

    # Total transactions
    c.execute("SELECT COUNT(*) FROM expenses")
    count = c.fetchone()[0]

    # Highest expense
    c.execute("SELECT MAX(amount) FROM expenses")
    max_expense = c.fetchone()[0] or 0

    # Most used category
    c.execute("""
        SELECT category, COUNT(*) 
        FROM expenses 
        GROUP BY category 
        ORDER BY COUNT(*) DESC 
        LIMIT 1
    """)
    top = c.fetchone()
    top_category = top[0] if top else "N/A"

    # Chart data
    c.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    chart_data = c.fetchall()

    conn.close()

    labels = [row[0] for row in chart_data]
    values = [row[1] for row in chart_data]

    return render_template("index.html",
                           expenses=data,
                           total=total,
                           count=count,
                           max_expense=max_expense,
                           top_category=top_category,
                           labels=labels,
                           values=values)

# Add expense
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']

        today = date.today().isoformat()   # ✅ NEW

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)",
            (title, amount, category, today)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template("add.html")

# Delete expense
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# Edit expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']

        c.execute("""
            UPDATE expenses 
            SET title=?, amount=?, category=? 
            WHERE id=?
        """, (title, amount, category, id))

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    # GET request → fetch data
    c.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = c.fetchone()
    conn.close()

    return render_template("edit.html", expense=expense)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)