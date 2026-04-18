# WealthWise 💰
### Personal Finance Portfolio Tracker

A full-stack personal finance tracker for small investors in India.

---

## 🗂️ Project Structure

```
wealthwise/
├── backend/
│   ├── app.py              ← Flask backend (API + auth)
│   └── requirements.txt    ← Python dependencies
└── frontend/
    ├── index.html          ← Login / Register page
    └── pages/
        └── dashboard.html  ← Main app (dashboard, goals, calculator)
```

---

## 🚀 Run Locally

### Step 1 – Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Server runs at: http://localhost:5000

### Step 2 – Frontend
Open browser → http://localhost:5000

---

## ☁️ Deploy for FREE

### Backend → Render.com (Free)
1. Push your code to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `python backend/app.py`
   - Root Directory: leave blank
5. Add environment variable:
   - `SECRET_KEY` = any random string (e.g. `mywealthwise2026secretkey`)
6. Click Deploy → Get your free URL (e.g. https://wealthwise.onrender.com)

### Frontend → Netlify (Free)
1. Go to https://netlify.com
2. Drag & drop the `frontend/` folder
3. Update API base URL in both HTML files:
   - Change `window.location.origin` → your Render URL
   - e.g. `const API = 'https://wealthwise.onrender.com';`
4. Your site is live at https://yourname.netlify.app

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/register | No | Register new user |
| POST | /api/login | No | Login, returns JWT token |
| GET | /api/me | Yes | Get current user info |
| POST | /api/portfolio | Yes | Add/update monthly data |
| GET | /api/portfolio | Yes | Get all portfolio entries |
| GET | /api/portfolio/export | Yes | Export as CSV |
| GET | /api/goals | Yes | Get all goals |
| POST | /api/goals | Yes | Add new goal |
| DELETE | /api/goals/:id | Yes | Delete a goal |

---

## 🗃️ Database Schema

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,       -- bcrypt hashed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio entries (one per user per month)
CREATE TABLE portfolio_entries (
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
    UNIQUE(user_id, year, month)  -- one entry per month per user
);

-- Goals
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    target_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✅ Features

- [x] User registration & login (JWT auth, bcrypt passwords)
- [x] Monthly portfolio data entry (8 asset types)
- [x] Dashboard with total portfolio, monthly growth %
- [x] Line chart – portfolio trend (last 12 months)
- [x] Pie/doughnut chart – asset allocation
- [x] Future Value calculator (compound growth formula)
- [x] Goal tracking with progress bars
- [x] Savings insights & allocation suggestions
- [x] CSV export
- [x] Monthly reminder
- [x] Mobile-friendly responsive design
- [x] Dark mode (always on, clean dark theme)

---

## 💰 Monetize Your Site

1. **Google AdSense** – Apply after publishing
2. **Affiliate links** – Groww, Zerodha partner programs  
3. **Premium features** – Charge for inflation-adjusted projection, alerts
4. **Newsletter** – Build email list, launch paid finance tips

---

## 🔧 Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js
- **Backend**: Python 3.x, Flask, Flask-CORS
- **Auth**: JWT (PyJWT) + bcrypt password hashing
- **Database**: SQLite (upgrade to PostgreSQL on Render for production)
- **Hosting**: Render (backend) + Netlify (frontend) — both FREE
