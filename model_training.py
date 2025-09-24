# model_training.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import json
from shapely.geometry import shape, Point
from shapely.ops import unary_union

print("Loading all Assam district boundaries from GeoJSON...")
geojson_path = 'static/assam_boundary.json'

try:
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    all_district_shapes = [shape(feature['geometry']) for feature in geojson_data['features']]
    assam_shape = unary_union(all_district_shapes)
    min_lon, min_lat, max_lon, max_lat = assam_shape.bounds
    print("✅ Successfully combined all district shapes.")

except Exception as e:
    print(f"Error processing GeoJSON file: {e}")
    exit()

print("Generating simulated training data...")
points_inside_assam = []
num_samples_to_find = 1000

while len(points_inside_assam) < num_samples_to_find:
    random_point = Point(np.random.uniform(min_lon, max_lon), np.random.uniform(min_lat, max_lat))
    if random_point.within(assam_shape):
        points_inside_assam.append(random_point)

data = {
    'latitude': [p.y for p in points_inside_assam],
    'longitude': [p.x for p in points_inside_assam],
    'elevation_m': np.random.randint(50, 800, len(points_inside_assam)),
    'proximity_to_river_km': np.random.uniform(0.1, 10, len(points_inside_assam)),
    'rainfall_mm': np.random.randint(0, 150, len(points_inside_assam)),
    'is_forest': np.random.choice([0, 1], len(points_inside_assam), p=[0.6, 0.4])
}
df = pd.DataFrame(data)

def determine_zone(row):
    if row['rainfall_mm'] > 120 and row['proximity_to_river_km'] < 1.5: return 2 # Red
    elif (row['rainfall_mm'] > 60 and row['is_forest'] == 1): return 1 # Orange
    else: return 0 # Green

df['zone'] = df.apply(determine_zone, axis=1)

X = df.drop(['zone', 'latitude', 'longitude'], axis=1)
y = df['zone']
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, 'risk_model.joblib')
print("✅ Model training complete!")