from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
from PyPDF2 import PdfReader
from db import connection, cursor

app = Flask(__name__)
app.secret_key = "my_secret_key_123"

# -----------------------------
# Upload folder setup
# -----------------------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------------
# Home Page (Dashboard)
# -----------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html", user=session["user"])


# -----------------------------
# Login Page
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        sql = "SELECT * FROM users WHERE email=%s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):

            session["user"] = user[1]  # full_name
            return redirect(url_for("home"))

        else:
            return """
            <h2>❌ Invalid Email or Password!</h2>
            <br>
            <a href="/login">Try Again</a>
            """

    return render_template("login.html")


# -----------------------------
# Register Page
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        sql = """
        INSERT INTO users(full_name, email, password)
        VALUES(%s, %s, %s)
        """

        values = (full_name, email, hashed_password)

        cursor.execute(sql, values)
        connection.commit()

        return """
        <h2>✅ Registration Successful!</h2>
        <br>
        <a href="/login">Go to Login</a>
        """

    return render_template("register.html")


# -----------------------------
# Upload Resume + ATS Score
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect(url_for("login"))

    resume = request.files["resume"]
    job_description = request.form["job_description"]

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
    resume.save(filepath)

    reader = PdfReader(filepath)

    resume_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            resume_text += text

    # Normalize text
    resume_text = resume_text.lower()
    job_description = job_description.lower()

    # Convert to word sets
    resume_words = set(resume_text.split())
    job_words = set(job_description.split())

    # Match & missing words
    matched_words = resume_words.intersection(job_words)
    missing_words = job_words - resume_words

    # Suggestions
    suggestions = [
        f"Add '{word}' to your resume if you have this skill."
        for word in sorted(missing_words)
    ]

    # ATS Score calculation
    ats_score = int((len(matched_words) / len(job_words)) * 100) if job_words else 0

    # Progress bar color
    if ats_score >= 80:
        progress_color = "bg-success"
    elif ats_score >= 50:
        progress_color = "bg-warning"
    else:
        progress_color = "bg-danger"

    return render_template(
        "result.html",
        ats_score=ats_score,
        progress_color=progress_color,
        matched_words=sorted(matched_words),
        missing_words=sorted(missing_words),
        suggestions=suggestions,
        resume_text=resume_text,
        job_description=job_description
    )


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():

    print("LOGOUT CALLED")

    session.pop("user", None)

    print(session)

    return redirect(url_for("login"))


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)