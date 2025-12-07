import os
import re
import cv2
import pytesseract
import sqlite3
from datetime import datetime
from pytesseract import TesseractNotFoundError
from flask import Flask, render_template, request, send_from_directory

# --- Tesseract path (LOCAL MACHINE) ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)

# --- Paths / folders ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "history.db")


# ------------ DB INIT ------------

def init_db():
    """Create history table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT,
            processed_filename TEXT,
            mode TEXT,
            blur_level INTEGER,
            emails INTEGER,
            phones INTEGER,
            cards INTEGER,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


# ------------ HELPERS ------------

def get_kernel_from_level(level: int) -> tuple[int, int]:
    """
    Convert blur level (1–3) to Gaussian blur kernel size.
    Must be odd numbers.
    """
    if level <= 1:
        size = 21       # light
    elif level == 2:
        size = 45       # normal
    else:
        size = 75       # strong

    return (size, size)


def classify_sensitive(text: str):
    """
    Decide whether a piece of text looks like
    an email / phone / card number.
    Returns 'email', 'phone', 'card' or None.
    """
    t = text.strip()
    if not t:
        return None

    # Email pattern
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", t):
        return "email"

    # Only digits for numbers
    digits = re.sub(r"\D", "", t)
    if not digits:
        return None

    # Card-like number (12–19 digits)
    if 12 <= len(digits) <= 19:
        return "card"

    # Phone number (7–13 digits)
    if 7 <= len(digits) <= 13:
        return "phone"

    return None


# ------------ ROUTES ------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template("home.html")

    # POST: handle upload
    mode = request.form.get("mode", "face")

    blur_value = request.form.get("blur", "2")
    try:
        blur_level = int(blur_value)
    except ValueError:
        blur_level = 2

    kernel = get_kernel_from_level(blur_level)

    file = request.files.get("image")
    if not file:
        return "No file uploaded", 400

    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)

    image = cv2.imread(original_path)
    if image is None:
        return "Could not read image file", 400

    sensitive_counts = None  # for text mode

    # ------------- MODE: FULL BLUR -------------
    if mode == "full":
        blurred_image = cv2.GaussianBlur(image, kernel, 0)
        suffix = "_fullblur"

    # ------------- MODE: FACE BLUR -------------
    elif mode == "face":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            # fallback: blur full image
            blurred_image = cv2.GaussianBlur(image, kernel, 0)
            suffix = "_fullblur"
        else:
            for (x, y, w, h) in faces:
                roi = image[y:y+h, x:x+w]
                blurred_face = cv2.GaussianBlur(roi, kernel, 0)
                image[y:y+h, x:x+w] = blurred_face

            blurred_image = image
            suffix = "_faceblur"

    # ------------- MODE: TEXT BLUR (OCR + SENSITIVE) -------------
    elif mode == "text":
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

            n_boxes = len(data["text"])
            sensitive_counts = {"email": 0, "phone": 0, "card": 0}
            blurred_any_sensitive = False

            # First pass: blur only sensitive info
            for i in range(n_boxes):
                try:
                    conf = int(data["conf"][i])
                except ValueError:
                    continue

                if conf <= 60:
                    continue

                raw_text = data["text"][i]
                category = classify_sensitive(raw_text)

                if category is None:
                    continue

                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]

                roi = image[y:y+h, x:x+w]
                blurred_roi = cv2.GaussianBlur(roi, kernel, 0)
                image[y:y+h, x:x+w] = blurred_roi

                sensitive_counts[category] += 1
                blurred_any_sensitive = True

            # If no sensitive text found → blur all detected text
            if not blurred_any_sensitive:
                for i in range(n_boxes):
                    try:
                        conf = int(data["conf"][i])
                    except ValueError:
                        continue

                    if conf <= 60:
                        continue

                    x = data["left"][i]
                    y = data["top"][i]
                    w = data["width"][i]
                    h = data["height"][i]

                    roi = image[y:y+h, x:x+w]
                    blurred_roi = cv2.GaussianBlur(roi, kernel, 0)
                    image[y:y+h, x:x+w] = blurred_roi

                sensitive_counts = None

            blurred_image = image
            suffix = "_textblur"

        except TesseractNotFoundError:
            # Server pe agar Tesseract nahi mila to crash na ho
            blurred_image = cv2.GaussianBlur(image, kernel, 0)
            suffix = "_fullblur"
            sensitive_counts = None

    # ------------- UNKNOWN MODE → fallback -------------
    else:
        blurred_image = cv2.GaussianBlur(image, kernel, 0)
        suffix = "_fullblur"

    # ------------- SAVE OUTPUT -------------
    name, ext = os.path.splitext(file.filename)
    output_filename = f"{name}{suffix}{ext}"
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)

    cv2.imwrite(output_path, blurred_image)

    # ------------- SAVE HISTORY (SQLite) -------------
    emails = phones = cards = None
    if isinstance(sensitive_counts, dict):
        emails = sensitive_counts.get("email", 0)
        phones = sensitive_counts.get("phone", 0)
        cards = sensitive_counts.get("card", 0)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO history (
            original_filename,
            processed_filename,
            mode,
            blur_level,
            emails,
            phones,
            cards,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file.filename,
            output_filename,
            mode,
            blur_level,
            emails,
            phones,
            cards,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        filename=output_filename,
        original_filename=file.filename,
        mode=mode,
        sensitive_counts=sensitive_counts,
    )


@app.route("/history")
def history():
    """Show last 50 processed images."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            original_filename,
            processed_filename,
            mode,
            blur_level,
            emails,
            phones,
            cards,
            created_at
        FROM history
        ORDER BY id DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()

    records = []
    for row in rows:
        records.append(
            {
                "original": row[0],
                "processed": row[1],
                "mode": row[2],
                "blur_level": row[3],
                "emails": row[4],
                "phones": row[5],
                "cards": row[6],
                "created_at": row[7],
            }
        )

    return render_template("history.html", records=records)


if __name__ == "__main__":
    app.run(debug=True)
