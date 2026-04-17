from flask import Flask, render_template, request, redirect
import sqlite3

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
            return redirect('/dashboard')   # ✅ FIXED
        else:
            return "Invalid credentials"

    return render_template("login.html")

# Redirect root → login
@app.route('/')
def home():
    return render_template("login.html")

# Dashboard
@app.route('/dashboard')
def index():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔥 NEW: Filters
    date = request.args.get('date')
    category = request.args.get('category')

    query = "SELECT * FROM expenses"
    params = []

    if date:
        query += " WHERE date=?"
        params.append(date)

    if category:
        if "WHERE" in query:
            query += " AND category=?"
        else:
            query += " WHERE category=?"
        params.append(category)

    c.execute(query, params)
    data = c.fetchall()

    # Total expense
    c.execute("SELECT SUM(amount) FROM expenses")
    total = c.fetchone()[0]
    if total is None:
        total = 0

    # Chart data
    c.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    chart_data = c.fetchall()

    conn.close()

    labels = [row[0] for row in chart_data]
    values = [row[1] for row in chart_data]

    return render_template("index.html",
                           expenses=data,
                           total=total,
                           labels=labels,
                           values=values)
# Add expense
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
       

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO expenses (title, amount, category) VALUES (?, ?, ?)",
            (title, amount, category)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')   # ✅ FIXED

    return render_template("add.html")

# Delete expense
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')   # ✅ FIXED

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)