# admin.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import time

app = Flask(__name__)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/add_override', methods=['POST'])
def add_override():
    geojson_str = request.form['geojson_data']
    risk_level = int(request.form['risk_level'])
    duration_hours = float(request.form['duration_hours'])
    
    expiry_timestamp = time.time() + (duration_hours * 3600)
    
    conn = sqlite3.connect('overrides.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO zone_overrides (geojson_str, risk_level, expiry_timestamp) VALUES (?, ?, ?)",
        (geojson_str, risk_level, expiry_timestamp)
    )
    conn.commit()
    conn.close()
    
    print(f"✅ New override added: Risk Level {risk_level} for {duration_hours} hours.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(port=5001, debug=True)