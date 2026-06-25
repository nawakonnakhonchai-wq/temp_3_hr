import json
import os
import geojson
from datetime import datetime

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
        raw_date = props.get('date')
        
        if not raw_date: 
            continue
            
        # แปลงวันที่จาก MM/DD/YYYY เป็น YYYY-MM-DD เพื่อให้ ArcGIS มองเป็น Date
        try:
            formatted_date = datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            formatted_date = raw_date # ถ้า format เดิมไม่ใช่ MM/DD/YYYY ให้ใช้ค่าเดิม
            
        if formatted_date not in daily_data: 
            daily_data[formatted_date] = []
        daily_data[formatted_date].append(f)
            
    summary_features = []
    for date, items in daily_data.items():
        valid_temps = [
            i for i in items 
            if i.get('properties', {}).get('temp') is not None
        ]
        
        if not valid_temps: 
            continue
        
        min_f = min(valid_temps, key=lambda x: x['properties'].get('temp', 999.0))
        max_f = max(valid_temps, key=lambda x: x['properties'].get('temp', -999.0))
        max_r24 = max(items, key=lambda x: x.get('properties', {}).get('rainfall_24hr', 0.0))
        
        # ฟังก์ชันช่วยสร้าง Feature เพื่อลดความซ้ำซ้อนของโค้ด
        def create_feature(item, metric, value, date_val):
            return geojson.Feature(geometry=item.get('geometry'), properties={
                "date": date_val, 
                "metric": metric, 
                "value": value, 
                "station": item['properties'].get('station_name', 'Unknown'), 
                "province": item['properties'].get('province', 'Unknown')
            })

        summary_features.append(create_feature(min_f, "min_temp", min_f['properties'].get('temp'), date))
        summary_features.append(create_feature(max_f, "max_temp", max_f['properties'].get('temp'), date))
        summary_features.append(create_feature(max_r24, "max_rainfall_24hr", max_r24['properties'].get('rainfall_24hr', 0.0), date))
        
    with open('stats/daily_summary.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(summary_features), f, ensure_ascii=False, indent=2)
    print("Daily summary generated successfully with ISO date format!")

if __name__ == "__main__":
    generate_summary()
