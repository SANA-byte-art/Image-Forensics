import sqlite3

def init_db():
    conn = sqlite3.connect('forensic.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            prediction TEXT,
            confidence REAL,
            timestamp TEXT,
            image_path TEXT
        )
    ''')

    conn.commit()
    conn.close()

def insert_result(filename, prediction, confidence, image_path):
    conn = sqlite3.connect('forensic.db')
    c = conn.cursor()

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute('''
        INSERT INTO analysis_results 
        (filename, prediction, confidence, timestamp, image_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, prediction, confidence, timestamp, image_path))

    conn.commit()
    conn.close()
