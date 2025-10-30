# Library Management – Full-Stack Project

A simple Library Management system with:
- **Backend:** java + SQLite (via SQLAlchemy), RESTful APIs, CORS enabled.
- **Frontend:** Vanilla HTML/CSS/JS using `fetch` to call the backend.
- **Features:** Manage Books, Members, and Loans (Issue/Return), Search, Basic validation.

## Quick Start

### Prereqs
- Python 3.9+ installed

### Setup & Run (Backend)
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python app.py
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Backend will start at `http://127.0.0.1:5000`

### Open Frontend
Open `frontend/index.html` in your browser.
> If you get CORS or mixed content issues, use a simple static server:
```bash
# From the frontend folder:
python -m http.server 5500
```
Then visit `http://127.0.0.1:5500`

### Default Endpoints (examples)
- `GET /api/books` – list books, `?q=term` to search
- `POST /api/books` – create book `{title, author, isbn, copies}`
- `PUT /api/books/<id>` – update
- `DELETE /api/books/<id>` – delete

- `GET /api/members`
- `POST /api/members` – `{name, email}`

- `POST /api/loans/issue` – `{book_id, member_id}`
- `POST /api/loans/return` – `{loan_id}`

### Notes
- The database file `library.db` is created automatically on first run.
- Simple validations are applied (e.g., non-empty fields, available copies).
- This is a template to learn/extend: add auth, pagination, or staff roles as needed.
