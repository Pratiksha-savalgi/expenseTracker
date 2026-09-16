# Expense Tracker — Simple Requirements

This is a **basic** version. One page. No heavy process.

## What we are building

A small website where a person can **add and manage their own expenses**.

**Tech:** HTML, CSS, JavaScript (frontend) · Flask (backend) · SQLite (database)

---

## Who uses it

One kind of user: a person with a login who tracks only **their** expenses.

---

## Features (v1 — keep it small)

1. **Register** — create an account (username + password)
2. **Login / Logout**
3. **Add expense** — amount, date, category, optional note
4. **See my expenses** — list only my rows
5. **Edit** an expense
6. **Delete** an expense
7. **Filter** by date and/or category (simple)
8. **Show total** of the expenses currently on screen

### Not in v1 (skip for now)

- Charts, budgets, bank sync, sharing with family, export, multi-currency

---

## Data we need (simple)

### User
- id
- username
- password (stored hashed, not plain text)
- created_at

### Expense
- id
- user_id (who owns it)
- amount
- date
- category (e.g. Food, Transport, Other)
- note (optional)
- created_at

---

## Simple rules

- You must be logged in to see or change expenses.
- You can only see/edit/delete **your** expenses.
- Amount must be greater than 0.
- Category is chosen from a short fixed list.

---

## Done when

- I can register, log in, add an expense, see it, edit it, delete it.
- Totals and filters work in a basic way.
- Another account cannot see my expenses.

---

## Next step

When you are happy with this list, we design the screens + database, then write the Flask app.
