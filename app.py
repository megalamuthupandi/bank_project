from flask import Flask, render_template, request, redirect, session
import mysql.connector
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key
app.secret_key = os.getenv("SECRET_KEY", "bank_secret_key")


# ---------------- DB Connection ----------------

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "bank_db"),
        port=int(os.getenv("DB_PORT", 3306))
    )


# ---------------- Home ----------------

@app.route("/")
def home():
    return redirect("/login")


# ---------------- Register ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        aadhaar = request.form["aadhaar"]
        password = generate_password_hash(request.form["password"])
        initial_amt = float(request.form["amount"])

        account_no = random.randint(1000000000, 9999999999)

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            INSERT INTO users
            (account_no, aadhaar_no, name, email, phone, password, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                account_no,
                aadhaar,
                name,
                email,
                phone,
                password,
                initial_amt
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return f"✅ Account created successfully! Your Account No: {account_no}"

    return render_template("register.html")


# ---------------- Login ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["user_id"]

            return redirect("/dashboard")

        else:
            return "❌ Invalid email or password!"

    return render_template("login.html")


# ---------------- Dashboard ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE user_id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        user=user
    )


# ---------------- Deposit ----------------

@app.route("/deposit", methods=["POST"])
def deposit():

    if "user_id" not in session:
        return redirect("/login")

    amount = float(request.form["amount"])

    if amount <= 0:
        return "❌ Deposit amount must be greater than 0"

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + %s
        WHERE user_id = %s
        """,
        (amount, session["user_id"])
    )

    cursor.execute(
        """
        INSERT INTO transactions
        (user_id, type, amount)
        VALUES (%s, 'Deposit', %s)
        """,
        (session["user_id"], amount)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect("/dashboard")


# ---------------- Withdraw ----------------

@app.route("/withdraw", methods=["POST"])
def withdraw():

    if "user_id" not in session:
        return redirect("/login")

    amount = float(request.form["amount"])

    if amount <= 0:
        return "❌ Withdrawal amount must be greater than 0"

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()
        return "❌ User not found"

    balance = float(user["balance"])

    if balance >= amount:

        cursor.execute(
            """
            UPDATE users
            SET balance = balance - %s
            WHERE user_id=%s
            """,
            (amount, session["user_id"])
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (user_id, type, amount)
            VALUES (%s, 'Withdraw', %s)
            """,
            (session["user_id"], amount)
        )

        db.commit()

    else:

        cursor.close()
        db.close()

        return "❌ Insufficient Balance!"

    cursor.close()
    db.close()

    return redirect("/dashboard")


# ---------------- Transactions ----------------

@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id=%s
        ORDER BY txn_date DESC
        """,
        (session["user_id"],)
    )

    txns = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "transactions.html",
        txns=txns
    )


# ---------------- Logout ----------------

@app.route("/logout")
def logout():

    session.pop("user_id", None)

    return redirect("/login")


# ---------------- Run ----------------

if __name__ == "__main__":
    app.run(debug=True)