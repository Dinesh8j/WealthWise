"""
WealthWise - Personal Finance Tracker
Flask Backend with JWT Authentication
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import os
import csv
import io

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

SECRET_KEY = os.environ.get('SECRET_KEY', 'wealthwise-secret-key-change-in-production')
DB_PATH = os.environ.get('DB_PATH', 'wealthwise.db')

# ─────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS portfolio_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            bank_balance REAL DEFAULT 0,
            equity REAL DEFAULT 0,
            gold REAL DEFAULT 0,
            fixed_deposits REAL DEFAULT 0,
            money_lent REAL DEFAULT 0,
            ppf REAL DEFAULT 0,
            bonds REAL DEFAULT 0,
            other_assets REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, year, month)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────

def generate_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth[7:]
    return verify_token(token)

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(user, *args, **kwargs)
    return decorated

# ─────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# ─────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                       (name, email, hashed))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        token = generate_token(user_id, email)
        return jsonify({'token': token, 'name': name, 'email': email}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode(), user['password'].encode()):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user['id'], user['email'])
    return jsonify({'token': token, 'name': user['name'], 'email': user['email']})

@app.route('/api/me', methods=['GET'])
@require_auth
def me(user):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, created_at FROM users WHERE id = ?', (user['user_id'],))
    u = cursor.fetchone()
    conn.close()
    return jsonify(dict(u))

# ─────────────────────────────────────────
# PORTFOLIO ROUTES
# ─────────────────────────────────────────

@app.route('/api/portfolio', methods=['POST'])
@require_auth
def add_portfolio(user):
    data = request.json
    year = data.get('year', datetime.datetime.now().year)
    month = data.get('month', datetime.datetime.now().month)

    fields = ['bank_balance', 'equity', 'gold', 'fixed_deposits',
              'money_lent', 'ppf', 'bonds', 'other_assets']
    values = [float(data.get(f, 0)) for f in fields]
    notes = data.get('notes', '')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO portfolio_entries
            (user_id, year, month, bank_balance, equity, gold, fixed_deposits,
             money_lent, ppf, bonds, other_assets, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, year, month) DO UPDATE SET
                bank_balance=excluded.bank_balance,
                equity=excluded.equity,
                gold=excluded.gold,
                fixed_deposits=excluded.fixed_deposits,
                money_lent=excluded.money_lent,
                ppf=excluded.ppf,
                bonds=excluded.bonds,
                other_assets=excluded.other_assets,
                notes=excluded.notes
        ''', (user['user_id'], year, month, *values, notes))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Portfolio saved successfully'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
@require_auth
def get_portfolio(user):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM portfolio_entries
        WHERE user_id = ?
        ORDER BY year DESC, month DESC
        LIMIT 24
    ''', (user['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    entries = []
    for row in rows:
        d = dict(row)
        d['total'] = (d['bank_balance'] + d['equity'] + d['gold'] +
                      d['fixed_deposits'] + d['money_lent'] + d['ppf'] +
                      d['bonds'] + d['other_assets'])
        entries.append(d)

    # Calculate month-over-month change
    for i, entry in enumerate(entries):
        if i + 1 < len(entries):
            prev_total = entries[i + 1]['total']
            if prev_total > 0:
                entry['change_pct'] = round(((entry['total'] - prev_total) / prev_total) * 100, 2)
            else:
                entry['change_pct'] = 0
        else:
            entry['change_pct'] = 0

    return jsonify(entries)

@app.route('/api/portfolio/export', methods=['GET'])
@require_auth
def export_portfolio(user):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT year, month, bank_balance, equity, gold, fixed_deposits,
               money_lent, ppf, bonds, other_assets, notes
        FROM portfolio_entries WHERE user_id = ?
        ORDER BY year, month
    ''', (user['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Year', 'Month', 'Bank Balance', 'Equity', 'Gold',
                     'Fixed Deposits', 'Money Lent', 'PPF', 'Bonds', 'Other Assets',
                     'Total', 'Notes'])
    for row in rows:
        d = dict(row)
        total = (d['bank_balance'] + d['equity'] + d['gold'] + d['fixed_deposits'] +
                 d['money_lent'] + d['ppf'] + d['bonds'] + d['other_assets'])
        writer.writerow([d['year'], d['month'], d['bank_balance'], d['equity'],
                         d['gold'], d['fixed_deposits'], d['money_lent'], d['ppf'],
                         d['bonds'], d['other_assets'], total, d['notes']])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=wealthwise_portfolio.csv'}
    )

# ─────────────────────────────────────────
# GOALS ROUTES
# ─────────────────────────────────────────

@app.route('/api/goals', methods=['GET'])
@require_auth
def get_goals(user):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC', (user['user_id'],))
    goals = [dict(g) for g in cursor.fetchall()]
    conn.close()
    return jsonify(goals)

@app.route('/api/goals', methods=['POST'])
@require_auth
def add_goal(user):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO goals (user_id, title, target_amount, current_amount, target_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user['user_id'], data['title'], data['target_amount'],
          data.get('current_amount', 0), data.get('target_date', '')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Goal added'}), 201

@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@require_auth
def delete_goal(user, goal_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM goals WHERE id = ? AND user_id = ?', (goal_id, user['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Goal deleted'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
