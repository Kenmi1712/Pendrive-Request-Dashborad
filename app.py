from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ip TEXT,
        purpose TEXT,
        status TEXT,
        request_time DATETIME,
        accept_time DATETIME,
        return_time DATETIME,
        position INTEGER
    )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_next_position(conn):
    result = conn.execute('SELECT MAX(position) FROM requests WHERE status IN ("queued", "pending")').fetchone()
    return (result[0] or 0) + 1

@app.route('/')
def user_dashboard():
    user_ip = request.remote_addr
    conn = get_db()
    logs = conn.execute(
        "SELECT request_time as timestamp, username, purpose, status, position FROM requests WHERE ip=? ORDER BY request_time DESC LIMIT 20",
        (user_ip,)
    ).fetchall()
    current = conn.execute(
        "SELECT * FROM requests WHERE status='accepted' AND return_time IS NULL ORDER BY accept_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return render_template('user.html', current=current, logs=logs, user_ip=user_ip)

@app.route('/request', methods=['POST'])
def request_pendrive():
    username = request.form['username']
    purpose = request.form['purpose']
    ip_addr = request.remote_addr
    conn = get_db()
    active = conn.execute("SELECT * FROM requests WHERE status='accepted' AND return_time IS NULL").fetchone()

    if active:
        # Add to queue as 'queued'
        position = get_next_position(conn)
        conn.execute(
            "INSERT INTO requests (username, ip, purpose, status, request_time, position) VALUES (?, ?, ?, ?, ?, ?)",
            (username, ip_addr, purpose, 'queued', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), position)
        )
        conn.commit()
        conn.close()
        flash(f'Pendrive is with someone else. You have been added to the queue at position #{position}.', 'info')
        return redirect(url_for('user_dashboard'))
    else:
        # No one has pendrive, status 'pending'
        conn.execute(
            "INSERT INTO requests (username, ip, purpose, status, request_time, position) VALUES (?, ?, ?, ?, ?, ?)",
            (username, ip_addr, purpose, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1)
        )
        conn.commit()
        conn.close()
        flash(f'Request sent to admin! (From IP: {ip_addr})', 'success')
        return redirect(url_for('user_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'Mihir@1712':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    requests = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
    current = conn.execute(
        "SELECT * FROM requests WHERE status='accepted' AND return_time IS NULL ORDER BY accept_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return render_template('admin_dashboard.html', requests=requests, current=current)

@app.route('/admin/accept/<int:id>')
def admin_accept(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute(
        "UPDATE requests SET status='accepted', accept_time=? WHERE id=?",
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:id>')
def admin_reject(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute("UPDATE requests SET status='rejected' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/return/<int:id>')
def admin_return(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute(
        "UPDATE requests SET return_time=? WHERE id=?",
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id)
    )
    # Promote next in queue
    next_in_queue = conn.execute(
        "SELECT id FROM requests WHERE status='queued' ORDER BY position ASC LIMIT 1"
    ).fetchone()
    if next_in_queue:
        conn.execute(
            "UPDATE requests SET status='pending', position=1 WHERE id=?",
            (next_in_queue['id'],)
        )
        # Decrement position of others
        conn.execute(
            "UPDATE requests SET position=position-1 WHERE status='queued' AND id != ?",
            (next_in_queue['id'],)
        )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=2712)