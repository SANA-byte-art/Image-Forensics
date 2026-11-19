import os
import webbrowser
import sqlite3
import io
import datetime

from flask import Flask, render_template, request, jsonify, send_file, redirect,session,flash
from werkzeug.security import generate_password_hash, check_password_hash
from model_utils import predict_image
from history_manager import save_case
from database import init_db, insert_result
from PIL import Image as PILImage
from video_utils import predict_video

# ReportLab Imports
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable is not set")

# =========================
# DATABASE INITIALIZATION
# =========================

init_db()

def init_user_table():
    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)

    conn.commit()
    conn.close()

init_user_table()

# TEMP ADMIN SETUP (RUN ONCE)
def make_admin():
    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()
    admin_email = os.environ.get("ADMIN_EMAIL")
    if not admin_email:
         raise RuntimeError("ADMIN_EMAIL environment variable is not set")
    cursor.execute(
        "UPDATE users SET role='admin' WHERE email=?",
        (admin_email,)
    )
    conn.commit()
    conn.close()
    print("Admin role granted!")

##make_admin()


def reset_users():
    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")

    conn.commit()
    conn.close()

    print("All users deleted successfully.")

##reset_users()

# =========================
# UPLOAD FOLDER
# =========================

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])



# =========================
# HOME ROUTES
# =========================

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")



# =========================
# DETECT ROUTES
# =========================

@app.route('/detect')
def detect():

    if 'user_id' not in session:
        return render_template("guest_detect_preview.html")

    return redirect('/dashboard')



# =========================
# AUTHENTICATION ROUTES
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Passwords do not match!")
            return redirect('/register')

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        try:
            conn = sqlite3.connect("forensic.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            conn.commit()
            conn.close()

            flash("Account created successfully! Please login.")
            return redirect('/login')

        except sqlite3.IntegrityError:
            flash("Email already exists!")
            return redirect('/register')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect("forensic.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, password, role FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):

            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            if user[3] == "admin":
                return redirect('/admin_dashboard')
            else:
                return redirect('/dashboard')

        else:
            flash("Invalid email or password!")
            return redirect('/login')

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# =========================
# PROTECTED DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template("dashboard.html")


@app.route('/admin_dashboard')
def admin_dashboard():

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    return render_template("admin_dashboard.html")



# =========================
# 🔥 PREDICTION ROUTE
# =========================

@app.route('/predict', methods=['POST'])
def predict():

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access"})

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"})

    file = request.files['image']

    if file.filename == "":
        return jsonify({"error": "No selected file"})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Convert TIFF images so browser can preview
    if filepath.lower().endswith(('.tif', '.tiff')):
        img = PILImage.open(filepath)
        new_path = filepath.rsplit('.', 1)[0] + ".jpg"
        img.convert("RGB").save(new_path)

        os.remove(filepath)   # remove original tif

        filepath = new_path
        filename = os.path.basename(new_path)
    else:
        filename = os.path.basename(filepath)

    label, confidence, top3 = predict_image(filepath)

    # Save JSON backup
    case_id = save_case(filename, label, confidence, top3)

    # Save to DB
    insert_result(
        filename=filename,
        prediction=label,
        confidence=float(confidence),
        image_path=filepath
    )

    return jsonify({
        "case_id": case_id,
        "label": label,
        "confidence": confidence,
        "top3": top3,
        "image": filename 
    })

#video predict

@app.route('/video_predict', methods=['POST'])
def video_predict():

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access"})

    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"})

    file = request.files['video']

    if file.filename == "":
        return jsonify({"error": "No selected file"})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    label, confidence = predict_video(filepath)

    return jsonify({
        "label": label,
        "confidence": confidence
    })

# =========================
# 🔥 HISTORY ROUTE (Filters)
# =========================

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/login')

    search_query = request.args.get("search", "")
    result_filter = request.args.get("result", "")
    risk_filter = request.args.get("risk", "")
    date_filter = request.args.get("date", "")

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    query = """
        SELECT id, filename, prediction, confidence, timestamp
        FROM analysis_results
        WHERE 1=1
    """

    params = []

    if search_query:
        query += " AND filename LIKE ?"
        params.append(f"%{search_query}%")

    if result_filter:
        query += " AND prediction = ?"
        params.append(result_filter)

    if date_filter:
        query += " AND DATE(timestamp) = ?"
        params.append(date_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    history_data = []

    for index, row in enumerate(rows, start=1):

        prediction = row[2]
        confidence = float(row[3])

        if prediction == "AI-Generated":
            risk = "HIGH"
        elif prediction == "Manipulated":
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if risk_filter and risk != risk_filter:
            continue

        history_data.append({
            "serial": index,
            "case_id": f"FX-{row[0]}",
            "image": row[1],
            "result": prediction,
            "risk": risk,
            "confidence": f"{confidence}%",
            "timestamp": row[4]
        })

    return render_template(
        "history.html",
        history=history_data,
        search=search_query,
        selected_result=result_filter,
        selected_risk=risk_filter,
        selected_date=date_filter
    )


# =========================
# 🔥 MODEL LOGS ROUTE
# =========================

@app.route('/model_logs')
def model_logs():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return render_template("admin_only.html")

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, prediction, confidence, timestamp
        FROM analysis_results
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    logs = []

    for row in rows:

        prediction = row[2]
        confidence = float(row[3])

        if prediction == "AI-Generated":
            risk = "HIGH"
        elif prediction == "Manipulated":
            risk = "MEDIUM"
        else:
            risk = "LOW"

        logs.append({
            "case_id": f"FX-{row[0]}",
            "image": row[1],
            "prediction": prediction,
            "confidence": f"{confidence}%",
            "risk": risk,
            "timestamp": row[4]
        })

    return render_template("model_logs.html", logs=logs)


# =========================
# 🔥 DELETE CASE ROUTE (NEW)
# =========================

@app.route('/delete_case/<case_id>', methods=['POST'])
def delete_case(case_id):

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    numeric_id = int(case_id.replace("FX-", ""))

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    # Get image path
    cursor.execute("""
        SELECT image_path FROM analysis_results
        WHERE id = ?
    """, (numeric_id,))

    row = cursor.fetchone()

    if row:
        image_path = row[0]

        # Delete image file
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        # Delete DB record
        cursor.execute("""
            DELETE FROM analysis_results
            WHERE id = ?
        """, (numeric_id,))
        conn.commit()

    conn.close()

    return redirect("/model_logs")


# =========================
# 🔥 ADVANCED REPORTS ANALYTICS DASHBOARD
# =========================

@app.route('/reports')
def reports():

    if 'user_id' not in session or session.get('role') != 'admin':
        return render_template("admin_only.html")

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prediction, confidence, timestamp
        FROM analysis_results
    """)

    rows = cursor.fetchall()
    conn.close()

    total_cases = len(rows)

    real_count = 0
    ai_count = 0
    manipulated_count = 0

    high_risk = 0
    medium_risk = 0
    low_risk = 0

    total_confidence = 0
    cases_per_day = {}

    for row in rows:
        prediction = row[0]
        confidence = float(row[1])
        timestamp = row[2]

        total_confidence += confidence

        # Prediction distribution
        if prediction == "Real":
            real_count += 1
            low_risk += 1
        elif prediction == "AI-Generated":
            ai_count += 1
            high_risk += 1
        elif prediction == "Manipulated":
            manipulated_count += 1
            medium_risk += 1

        # Timeline grouping
        date = timestamp.split(" ")[0]
        if date in cases_per_day:
            cases_per_day[date] += 1
        else:
            cases_per_day[date] = 1

    avg_confidence = round(total_confidence / total_cases, 2) if total_cases > 0 else 0

    return render_template(
        "reports.html",
        total_cases=total_cases,
        real_count=real_count,
        ai_count=ai_count,
        manipulated_count=manipulated_count,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        avg_confidence=avg_confidence,
        dates=list(cases_per_day.keys()),
        counts=list(cases_per_day.values())
    )


# =========================
# 🔥 REPORT ROUTE
# =========================

@app.route('/report/<case_id>')
def report(case_id):

    numeric_id = case_id.replace("FX-", "")

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, prediction, confidence, timestamp, image_path
        FROM analysis_results
        WHERE id = ?
    """, (numeric_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        case = {
            "case_id": f"FX-{row[0]}",
            "image": row[1],
            "result": row[2],
            "confidence": f"{row[3]}%",
            "timestamp": row[4],
            "image_path": row[5]
        }

        return render_template("report.html", case=case)

    return "Case not found"


# =========================
# 🔥 PROFESSIONAL PDF ROUTE
# =========================

@app.route('/download_report/<case_id>')
def download_report(case_id):

    numeric_id = case_id.replace("FX-", "")

    conn = sqlite3.connect("forensic.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, prediction, confidence, timestamp, image_path
        FROM analysis_results
        WHERE id = ?
    """, (numeric_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Case not found"

    case_id_full = f"FX-{row[0]}"
    filename = row[1]
    prediction = row[2]
    confidence = row[3]
    timestamp = row[4]
    image_path = row[5]

    if prediction == "AI-Generated":
        risk = "HIGH"
        risk_color = colors.red
    elif prediction == "Manipulated":
        risk = "MEDIUM"
        risk_color = colors.orange
    else:
        risk = "LOW"
        risk_color = colors.green

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>FORENSIX</b>", styles['Title']))
    elements.append(Paragraph("AI-Based Digital Image Forensic System", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("<b>Official Forensic Investigation Report</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Case ID", case_id_full],
        ["Image Name", filename],
        ["Prediction Result", prediction],
        ["Risk Level", risk],
        ["Confidence Score", f"{confidence}%"],
        ["Analysis Timestamp", timestamp],
        ["Report Generated On", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    ]

    table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (1, 3), (1, 3), risk_color),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.white),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

    if os.path.exists(image_path):
        elements.append(Paragraph("<b>Analyzed Image Preview:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.2 * inch))
        img = Image(image_path, width=4 * inch, height=4 * inch)
        elements.append(img)
        elements.append(Spacer(1, 0.3 * inch))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Authorized By: Digital Forensic Analysis Unit", styles['Normal']))
    elements.append(Paragraph("Signature: ____________________________", styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("FORENSIX © 2026 | Confidential Report", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"FORENSIX_Report_{case_id_full}.pdf",
        mimetype='application/pdf'
    )


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True) 