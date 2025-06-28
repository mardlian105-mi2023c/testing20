import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'rahasia'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            deskripsi TEXT,
            harga INTEGER,
            gambar TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    produk = conn.execute("SELECT * FROM produk").fetchall()
    conn.close()
    return render_template('index.html', produk=produk)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        harga = request.form['harga']
        file = request.files['gambar']

        if os.environ.get("VERCEL"):
            flash("Upload tidak disimpan di Vercel. Coba di local.")
            filename = "default.jpg"
        else:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        with sqlite3.connect('database.db') as conn:
            conn.execute("INSERT INTO produk (nama, deskripsi, harga, gambar) VALUES (?, ?, ?, ?)",
                         (nama, deskripsi, harga, filename))
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form['action']
        username = request.form['username']
        password = request.form['password']
        if action == 'register':
            try:
                with sqlite3.connect('database.db') as conn:
                    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                flash("Registrasi berhasil. Silakan login.")
                return redirect(url_for('auth'))
            except sqlite3.IntegrityError:
                flash("Username sudah digunakan.")
        elif action == 'login':
            with sqlite3.connect('database.db') as conn:
                user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect(url_for('index'))
            else:
                flash("Login gagal.")
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    conn = sqlite3.connect('database.db')
    produk = conn.execute("SELECT * FROM produk").fetchall()
    conn.close()
    return render_template('admin.html', produk=produk)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    conn = sqlite3.connect('database.db')
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        harga = request.form['harga']
        conn.execute("UPDATE produk SET nama=?, deskripsi=?, harga=? WHERE id=?", (nama, deskripsi, harga, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    produk = conn.execute("SELECT * FROM produk WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit.html', produk=produk)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    with sqlite3.connect('database.db') as conn:
        conn.execute("DELETE FROM produk WHERE id=?", (id,))
    return redirect(url_for('admin'))

# Untuk vercel deployment
app = app

if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    app.run(debug=True)
