import json
import os
import geojson

def generate_summary():
    os.makedirs('stats', exist_ok=True)
    history_file = 'history/weather_history.geojson'
    
    if not os.path.exists(history_file): return

    with open(history_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        features = data['features']
    
    # จัดกลุ่มข้อมูลรายวัน
    daily_data = {}
    for f in features:
        date = f['properties']['date']
        if date not in daily_data: daily_data[date] = []
        daily_data[date].append(f)
            
    summary_features = []
    for date, items in daily_data.items():
        valid_temps = [i for i in items if i['properties']['temp'] > 0]
        if not valid_temps: continue
        
        # หาสถานีที่ Min และ Max
        min_f = min(valid_temps, key=lambda x: x['properties']['temp'])
        max_f = max(valid_temps, key=lambda x: x['properties']['temp'])
        max_r = max(items, key=lambda x: x['properties']['rainfall'])
        
        # สร้าง Feature สรุปสำหรับ ArcGIS
        summary_features.append(geojson.Feature(geometry=min_f['geometry'], properties={
            "date": date, "metric": "min_temp", "value": min_f['properties']['temp'], 
            "station": min_f['properties']['station_name'], "province": min_f['properties']['province']
        }))
        summary_features.append(geojson.Feature(geometry=max_f['geometry'], properties={
            "date": date, "metric": "max_temp", "value": max_f['properties']['temp'], 
            "station": max_f['properties']['station_name'], "province": max_f['properties']['province']
        }))
        summary_features.append(geojson.Feature(geometry=max_r['geometry'], properties={
            "date": date, "metric": "max_rainfall", "value": max_r['properties']['rainfall'], 
            "station": max_r['properties']['station_name'], "province": max_r['properties']['province']
        }))
        
    with open('stats/daily_summary.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(summary_features), f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    generate_summary()
