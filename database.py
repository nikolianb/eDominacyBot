import sqlite3

def create_database():
    conn = sqlite3.connect('user_activities.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            user_id TEXT PRIMARY KEY,
            day INTEGER,
            has_worked INTEGER,
            has_rested INTEGER,
            has_worked_twice INTEGER,
            has_trained INTEGER
        )
    ''')
    conn.commit()
    conn.close()

create_database()
