# database_setup.py
import sqlite3

conn = sqlite3.connect('overrides.db')
cursor = conn.cursor()

print("Creating 'zone_overrides' table...")

cursor.execute('''
CREATE TABLE IF NOT EXISTS zone_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    geojson_str TEXT NOT NULL,
    risk_level INTEGER NOT NULL,
    expiry_timestamp REAL NOT NULL
);
''')

conn.commit()
conn.close()

print("✅ Database setup complete.")