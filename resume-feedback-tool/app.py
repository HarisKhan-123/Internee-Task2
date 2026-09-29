"""
AI Resume Feedback Tool
------------------------
Upload a resume (PDF or DOCX), extract its text, and get AI-generated
feedback on structure, skills, and improvement areas.

Uses Groq's free-tier API instead of the paid OpenAI API.
"""
import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.parser import extract_resume_text, ResumeParsingError
from utils.analyzer import analyze_resume, AnalysisError

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["resume"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a PDF or DOCX.")
        return redirect(url_for("index"))

    # Save with a unique name to avoid collisions
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
    file.save(saved_path)

    try:
        resume_text = extract_resume_text(saved_path)
        feedback = analyze_resume(resume_text)
    except ResumeParsingError as exc:
        flash(f"Could not read your resume: {exc}")
        return redirect(url_for("index"))
    except AnalysisError as exc:
        flash(f"Analysis failed: {exc}")
        return redirect(url_for("index"))
    finally:
        # Clean up the uploaded file — we don't need to keep it around
        try:
            os.remove(saved_path)
        except OSError:
            pass

    return render_template(
        "results.html",
        filename=original_name,
        feedback=feedback,
        resume_preview=resume_text[:600],
    )


@app.errorhandler(413)
def file_too_large(_e):
    flash("File is too large. Max size is 8 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
