"""
Simple personal expense tracker.
HTML/CSS/JS + Flask + SQLite
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "expense_tracker.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Housing",
    "Utilities",
    "Health",
    "Entertainment",
    "Shopping",
    "Education",
    "Other",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me-later")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "categories": CATEGORIES,
    }


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("expenses"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("expenses"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
        else:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if exists:
                flash("That username is already taken.", "error")
            else:
                db.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (
                        username,
                        generate_password_hash(password),
                        datetime.utcnow().isoformat(timespec="seconds"),
                    ),
                )
                db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("expenses"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("expenses"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))


@app.route("/expenses")
@login_required
def expenses():
    user_id = session["user_id"]
    date_from = (request.args.get("from") or "").strip()
    date_to = (request.args.get("to") or "").strip()
    category = (request.args.get("category") or "").strip()

    if date_from and date_to and date_from > date_to:
        flash("From date cannot be after To date.", "error")
        date_from = ""
        date_to = ""

    query = (
        "SELECT * FROM expenses WHERE user_id = ?"
    )
    params: list = [user_id]

    if date_from:
        query += " AND expense_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND expense_date <= ?"
        params.append(date_to)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY expense_date DESC, id DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    filtered_total = sum(float(r["amount"]) for r in rows)

    today = date.today()
    month_start = today.replace(day=1).isoformat()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    month_end = next_month.isoformat()

    month_row = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = ? AND expense_date >= ? AND expense_date < ?
        """,
        (user_id, month_start, month_end),
    ).fetchone()
    month_total = float(month_row["total"])

    return render_template(
        "expenses.html",
        expenses=rows,
        filtered_total=filtered_total,
        month_total=month_total,
        filters={
            "from": date_from,
            "to": date_to,
            "category": category or "All",
        },
    )


def _parse_expense_form():
    amount_raw = (request.form.get("amount") or "").strip()
    expense_date = (request.form.get("date") or "").strip()
    category = (request.form.get("category") or "").strip()
    note = (request.form.get("note") or "").strip() or None

    errors = []
    amount = None
    try:
        amount = float(amount_raw)
        if amount <= 0:
            errors.append("Amount must be greater than 0.")
    except ValueError:
        errors.append("Amount must be a number.")

    if not expense_date:
        errors.append("Date is required.")
    else:
        try:
            date.fromisoformat(expense_date)
        except ValueError:
            errors.append("Date is invalid.")

    if category not in CATEGORIES:
        errors.append("Choose a valid category.")

    return amount, expense_date, category, note, errors


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount, expense_date, category, note, errors = _parse_expense_form()
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "expense_form.html",
                mode="add",
                form={
                    "amount": request.form.get("amount", ""),
                    "date": request.form.get("date", ""),
                    "category": request.form.get("category", "Food"),
                    "note": request.form.get("note", ""),
                },
            )

        get_db().execute(
            """
            INSERT INTO expenses (user_id, amount, expense_date, category, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                amount,
                expense_date,
                category,
                note,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        get_db().commit()
        flash("Expense saved.", "success")
        return redirect(url_for("expenses"))

    return render_template(
        "expense_form.html",
        mode="add",
        form={
            "amount": "",
            "date": date.today().isoformat(),
            "category": "Food",
            "note": "",
        },
    )


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id: int):
    db = get_db()
    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    ).fetchone()
    if expense is None:
        flash("Expense not found.", "error")
        return redirect(url_for("expenses"))

    if request.method == "POST":
        amount, expense_date, category, note, errors = _parse_expense_form()
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "expense_form.html",
                mode="edit",
                expense_id=expense_id,
                form={
                    "amount": request.form.get("amount", ""),
                    "date": request.form.get("date", ""),
                    "category": request.form.get("category", "Food"),
                    "note": request.form.get("note", ""),
                },
            )

        db.execute(
            """
            UPDATE expenses
            SET amount = ?, expense_date = ?, category = ?, note = ?
            WHERE id = ? AND user_id = ?
            """,
            (amount, expense_date, category, note, expense_id, session["user_id"]),
        )
        db.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("expenses"))

    return render_template(
        "expense_form.html",
        mode="edit",
        expense_id=expense_id,
        form={
            "amount": expense["amount"],
            "date": expense["expense_date"],
            "category": expense["category"],
            "note": expense["note"] or "",
        },
    )


@app.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id: int):
    db = get_db()
    result = db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    )
    db.commit()
    if result.rowcount:
        flash("Expense deleted.", "success")
    else:
        flash("Expense not found.", "error")
    return redirect(url_for("expenses"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
