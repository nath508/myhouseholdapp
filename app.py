from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'super_secret_myhousehold_key_123'

def init_db():
    conn = sqlite3.connect('myhousehold.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS items 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, description TEXT, quantity INTEGER, available BOOLEAN, category TEXT)''')
    conn.commit()
    conn.close()

if not os.path.exists('myhousehold.db'):
    init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html', show_dashboard=False, email="")

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = sqlite3.connect('myhousehold.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['email'] = user[1]
        return redirect(url_for('dashboard'))
    return "<h3>Invalid credentials. <a href='/'>Try again</a></h3>"

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = sqlite3.connect('myhousehold.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        user_id = c.fetchone()[0]
        session['user_id'] = user_id
        session['email'] = email
        return redirect(url_for('dashboard'))
    except sqlite3.IntegrityError:
        return "<h3>Email already exists. <a href='/signup_page'>Try again</a></h3>"
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('login.html', show_dashboard=True, email=session['email'])

@app.route('/api/items', methods=['GET', 'POST'])
def handle_items():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    conn = sqlite3.connect('myhousehold.db')
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT * FROM items WHERE user_id=?", (user_id,))
        rows = c.fetchall()
        items = [{"id": r[0], "name": r[2], "description": r[3], "quantity": r[4], "available": bool(r[5]), "category": r[6]} for r in rows]
        conn.close()
        return jsonify(items)

    elif request.method == 'POST':
        data = request.json
        c.execute("DELETE FROM items WHERE user_id=?", (user_id,))
        for item in data:
            c.execute("INSERT INTO items (user_id, name, description, quantity, available, category) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, item['name'], item['description'], item['quantity'], item['available'], item['category']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
