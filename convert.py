import json
import os
import geojson

def generate_summary():
    os.makedirs('stats', exist_ok=True)
    history_file = 'history/weather_history.geojson'
    
    if not os.path.exists(history_file): 
        print(f"Error: {history_file} does not exist.")
        return

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            features = data.get('features', [])
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"Error reading history file: {e}")
        return
    
    daily_data = {}
    for f in features:
        props = f.get('properties', {})
        date = props.get('date')
        
        if not date: 
            continue
            
        if date not in daily_data: 
            daily_data[date] = []
        daily_data[date].append(f)
            
    summary_features = []
    for date, items in daily_data.items():
        # แก้ไขให้รองรับอุณหภูมิ 0 องศา หรือติดลบ (ตราบใดที่ค่านั้นมีอยู่จริง ไม่ใช่ None)
        valid_temps = [
            i for i in items 
            if i.get('properties', {}).get('temp') is not None
        ]
        
        if not valid_temps: 
            continue
        
        # ดึงค่าแบบใส่ Default ป้องกันกรณีเกิด KeyError ขึ้นภายหลัง
        min_f = min(valid_temps, key=lambda x: x['properties'].get('temp', 999.0))
        max_f = max(valid_temps, key=lambda x: x['properties'].get('temp', -999.0))
        max_r24 = max(items, key=lambda x: x.get('properties', {}).get('rainfall_24hr', 0.0))
        
        summary_features.append(geojson.Feature(geometry=min_f.get('geometry'), properties={
            "date": date, 
            "metric": "min_temp", 
            "value": min_f['properties'].get('temp'), 
            "station": min_f['properties'].get('station_name', 'Unknown'), 
            "province": min_f['properties'].get('province', 'Unknown')
        }))
        
        summary_features.append(geojson.Feature(geometry=max_f.get('geometry'), properties={
            "date": date, 
            "metric": "max_temp", 
            "value": max_f['properties'].get('temp'), 
            "station": max_f['properties'].get('station_name', 'Unknown'), 
            "province": max_f['properties'].get('province', 'Unknown')
        }))
        
        summary_features.append(geojson.Feature(geometry=max_r24.get('geometry'), properties={
            "date": date, 
            "metric": "max_rainfall_24hr", 
            "value": max_r24['properties'].get('rainfall_24hr', 0.0), 
            "station": max_r24['properties'].get('station_name', 'Unknown'), 
            "province": max_r24['properties'].get('province', 'Unknown')
        }))
        
    with open('stats/daily_summary.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(summary_features), f, ensure_ascii=False, indent=2)
    print("Daily summary generated successfully!")

if __name__ == "__main__":
    generate_summary()
