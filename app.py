import os
import sqlite3
import os
import time
from contextlib import contextmanager
from io import BytesIO
from xml.sax.saxutils import escape

from flask import Flask, redirect, render_template, request, send_file, url_for
import mysql.connector
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

app = Flask(__name__)


@contextmanager
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        database=os.environ.get("MYSQL_DATABASE", "notes"),
        user=os.environ.get("MYSQL_USER", "notes"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
    )
    try:
        yield connection
    except mysql.connector.Error:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()


def initialize_db():
    for attempt in range(30):
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS notes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        content LONGTEXT NOT NULL
                    ) CHARACTER SET utf8mb4"""
                )
                cursor.close()
            return
        except mysql.connector.Error:
            if attempt == 29:
                raise
            app.logger.warning("MySQL is not ready yet; retrying database setup.")
            time.sleep(2)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if title and content:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO notes (title, content) VALUES (%s, %s)",
                    (title, content),
                )
                cursor.close()
        return redirect(url_for("index"))

    with get_db_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM notes ORDER BY id DESC")
        notes = cursor.fetchall()
        cursor.close()
    return render_template("index.html", notes=notes)


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        cursor.close()
    return redirect(url_for("index"))


@app.route("/export")
def export_notes():
    with get_db_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT title, content FROM notes ORDER BY id DESC")
        notes = cursor.fetchall()
        cursor.close()

    pdf = BytesIO()
    document = SimpleDocTemplate(pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph("My Notes", styles["Title"]), Spacer(1, 16)]

    if notes:
        for note in notes:
            content = escape(note["content"]).replace("\r\n", "\n").replace("\n", "<br/>")
            elements.extend(
                [
                    Paragraph(escape(note["title"]), styles["Heading2"]),
                    Paragraph(content, styles["BodyText"]),
                    Spacer(1, 12),
                ]
            )
    else:
        elements.append(Paragraph("No notes yet.", styles["BodyText"]))

    document.build(elements)
    pdf.seek(0)
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="notes.pdf",
    )


if __name__ == "__main__":
    initialize_db()
    app.run(host="0.0.0.0", port=5000)
