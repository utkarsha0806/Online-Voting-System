import sqlite3

db = sqlite3.connect("data.db")
cursor = db.cursor()

cursor.execute('''
            CREATE TABLE IF NOT EXISTS faceData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                face_id INTERGER  UNIQUE NOT NULL
            )
        ''')
db.commit()
db.close()