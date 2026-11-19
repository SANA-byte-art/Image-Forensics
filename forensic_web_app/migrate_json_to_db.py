import json
import sqlite3

# Load JSON history
with open("history.json", "r") as f:
    history_data = json.load(f)

conn = sqlite3.connect("forensic.db")
cursor = conn.cursor()

for case in history_data:

    cursor.execute("""
        INSERT INTO analysis_results
        (filename, prediction, confidence, timestamp, image_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        case["image"],                     # JSON uses "image"
        case["label"],                     # JSON uses "label"
        float(case["confidence"]),
        case["timestamp"],
        f"static/uploads/{case['image']}"
    ))

conn.commit()
conn.close()

print("Migration completed successfully!")
