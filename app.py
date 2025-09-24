# app.py (UPDATED with anti-caching headers)
from flask import Flask, render_template, jsonify, make_response # Import make_response
import pandas as pd
import numpy as np
import joblib
import json
import sqlite3
import time
from shapely.geometry import shape, Point
from shapely.ops import unary_union

app = Flask(__name__)
model = joblib.load('risk_model.joblib')

with open('static/assam_boundary.json') as f:
    assam_geojson_data = json.load(f)
all_shapes = [shape(feature['geometry']) for feature in assam_geojson_data['features']]
assam_shape = unary_union(all_shapes)
min_lon, min_lat, max_lon, max_lat = assam_shape.bounds

def get_mock_features(lat, lon):
    return { 'latitude': lat, 'longitude': lon, 'elevation_m': np.random.randint(50, 800), 'proximity_to_river_km': np.random.uniform(0.1, 10), 'rainfall_mm': np.random.randint(0, 150), 'is_forest': np.random.choice([0, 1], p=[0.6, 0.4]) }

def get_active_overrides():
    conn = sqlite3.connect('overrides.db')
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute("SELECT geojson_str, risk_level FROM zone_overrides WHERE expiry_timestamp > ?", (current_time,))
    overrides = [{"shape": shape(json.loads(row[0])), "risk_level": row[1]} for row in cursor.fetchall()]
    conn.close()
    return overrides

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/get_risk_data')
def get_risk_data():
    active_overrides = get_active_overrides()
    
    points_to_predict = []
    for lat in np.arange(min_lat, max_lat, 0.08):
        for lon in np.arange(min_lon, max_lon, 0.08):
            point = Point(lon, lat)
            if point.within(assam_shape):
                points_to_predict.append(get_mock_features(lat, lon))
    
    df_predict = pd.DataFrame(points_to_predict)
    if not df_predict.empty:
        features_for_model = df_predict.drop(['latitude', 'longitude'], axis=1)
        df_predict['zone'] = model.predict(features_for_model)
        
        for i, row in df_predict.iterrows():
            point = Point(row['longitude'], row['latitude'])
            for override in active_overrides:
                if point.within(override['shape']):
                    df_predict.at[i, 'zone'] = override['risk_level']
                    break
    
    # --- THIS IS THE MODIFIED PART ---
    # Create a response and add headers to prevent caching
    response = make_response(jsonify(df_predict.to_dict(orient='records')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response
    # --- END OF MODIFIED PART ---

if __name__ == '__main__':
    app.run(debug=True)