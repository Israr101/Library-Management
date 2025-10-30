import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, Book, Member, Loan

DB_URL = os.environ.get("DB_URL", "sqlite:///library.db")

app = Flask(__name__)
CORS(app)

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
Base.metadata.create_all(engine)

SessionLocal = scoped_session(sessionmaker(bind=engine))

def get_session():
    return SessionLocal()

# Helpers
def book_to_dict(b: Book):
    active_loans = sum(1 for L in b.loans if L.returned_at is None)
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "isbn": b.isbn,
        "copies": b.copies,
        "available": max(b.copies - active_loans, 0),
        "created_at": b.created_at.isoformat()
    }

def member_to_dict(m: Member):
    return {
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "created_at": m.created_at.isoformat()
    }

def loan_to_dict(l: Loan):
    return {
        "id": l.id,
        "book_id": l.book_id,
        "member_id": l.member_id,
        "issued_at": l.issued_at.isoformat(),
        "returned_at": l.returned_at.isoformat() if l.returned_at else None,
        "book_title": l.book.title if l.book else None,
        "member_name": l.member.name if l.member else None
    }

@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()

@app.get("/api/health")
def health():
    return {"status": "ok"}

# Books
@app.get("/api/books")
def list_books():
    q = request.args.get("q", "").strip()
    s = get_session()
    try:
        stmt = select(Book)
        if q:
            stmt = stmt.where(or_(Book.title.ilike(f"%{q}%"), Book.author.ilike(f"%{q}%"), Book.isbn.ilike(f"%{q}%")))
        books = s.scalars(stmt.order_by(Book.created_at.desc())).all()
        return jsonify([book_to_dict(b) for b in books])
    finally:
        s.close()

@app.post("/api/books")
def create_book():
    data = request.get_json(force=True)
    for field in ["title", "author", "isbn", "copies"]:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            return jsonify({"error": f"Missing or empty field: {field}"}), 400
    s = get_session()
    try:
        if s.scalar(select(Book).where(Book.isbn == data["isbn"])):
            return jsonify({"error": "ISBN already exists"}), 400
        book = Book(title=data["title"].strip(), author=data["author"].strip(), isbn=data["isbn"].strip(), copies=int(data["copies"]))
        s.add(book)
        s.commit()
        s.refresh(book)
        return jsonify(book_to_dict(book)), 201
    finally:
        s.close()

@app.put("/api/books/<int:book_id>")
def update_book(book_id: int):
    data = request.get_json(force=True)
    s = get_session()
    try:
        book = s.get(Book, book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404
        for key in ["title", "author", "isbn", "copies"]:
            if key in data:
                val = data[key]
                if key in ["title", "author", "isbn"] and isinstance(val, str):
                    val = val.strip()
                if key == "copies":
                    val = int(val)
                setattr(book, key, val)
        s.commit()
        return jsonify(book_to_dict(book))
    finally:
        s.close()

@app.delete("/api/books/<int:book_id>")
def delete_book(book_id: int):
    s = get_session()
    try:
        book = s.get(Book, book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404
        s.delete(book)
        s.commit()
        return jsonify({"ok": True})
    finally:
        s.close()

# Members
@app.get("/api/members")
def list_members():
    s = get_session()
    try:
        members = s.scalars(select(Member).order_by(Member.created_at.desc())).all()
        return jsonify([member_to_dict(m) for m in members])
    finally:
        s.close()

@app.post("/api/members")
def create_member():
    data = request.get_json(force=True)
    for field in ["name", "email"]:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            return jsonify({"error": f"Missing or empty field: {field}"}), 400
    s = get_session()
    try:
        if s.scalar(select(Member).where(Member.email == data["email"].strip())):
            return jsonify({"error": "Email already exists"}), 400
        m = Member(name=data["name"].strip(), email=data["email"].strip())
        s.add(m)
        s.commit()
        s.refresh(m)
        return jsonify(member_to_dict(m)), 201
    finally:
        s.close()

# Loans
@app.get("/api/loans")
def list_loans():
    s = get_session()
    try:
        loans = s.scalars(select(Loan).order_by(Loan.issued_at.desc())).all()
        return jsonify([loan_to_dict(l) for l in loans])
    finally:
        s.close()

@app.post("/api/loans/issue")
def issue_loan():
    data = request.get_json(force=True)
    for field in ["book_id", "member_id"]:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    s = get_session()
    try:
        book = s.get(Book, int(data["book_id"]))
        member = s.get(Member, int(data["member_id"]))
        if not book or not member:
            return jsonify({"error": "Invalid book or member"}), 400
        active_loans = s.scalars(select(Loan).where(Loan.book_id == book.id, Loan.returned_at.is_(None))).all()
        if len(active_loans) >= book.copies:
            return jsonify({"error": "No available copies"}), 400
        loan = Loan(book_id=book.id, member_id=member.id)
        s.add(loan)
        s.commit()
        s.refresh(loan)
        return jsonify(loan_to_dict(loan)), 201
    finally:
        s.close()

@app.post("/api/loans/return")
def return_loan():
    data = request.get_json(force=True)
    if "loan_id" not in data:
        return jsonify({"error": "Missing field: loan_id"}), 400
    s = get_session()
    try:
        loan = s.get(Loan, int(data["loan_id"]))
        if not loan:
            return jsonify({"error": "Loan not found"}), 404
        if loan.returned_at is not None:
            return jsonify({"error": "Loan already returned"}), 400
        loan.returned_at = datetime.utcnow()
        s.commit()
        return jsonify(loan_to_dict(loan))
    finally:
        s.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
