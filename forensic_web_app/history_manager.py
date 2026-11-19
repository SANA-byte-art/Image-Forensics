import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"


def generate_case_id():
    return "FX-" + datetime.now().strftime("%Y%m%d%H%M%S")


def save_case(image_name, label, confidence, top3):

    case_id = generate_case_id()

    # Risk Classification
    if label == "AI-Generated":
        risk = "HIGH"
    elif label == "Manipulated":
        risk = "MEDIUM"
    else:
        risk = "LOW"

    case_data = {
        "case_id": case_id,
        "image": image_name,
        "label": label,
        "confidence": round(float(confidence), 2),
        "risk": risk,
        "top3": top3,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_version": "CNN v1.0"
    }

    # Load existing history safely
    history = []

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            # If file corrupted, reset safely
            history = []

    # Insert newest case at top
    history.insert(0, case_data)

    # Save back to file
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    return case_id


def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except json.JSONDecodeError:
        return []

    # Ensure old entries don't break report page
    for case in history:
        case.setdefault("risk", "N/A")
        case.setdefault("model_version", "CNN v1.0")

    return history
