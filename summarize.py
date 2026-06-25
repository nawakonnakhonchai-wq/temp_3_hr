import json
import os
import geojson

def generate_summary():
    os.makedirs('stats', exist_ok=True)
    history_file = 'history/weather_history.geojson'
    
    if not os.path.exists(history_file): 
        print(f"Error: {history_file} does not exist.")
        return

    # ป้องกันไฟล์พัง หรือโครงสร้างไม่ใช่ GeoJSON ที่ถูกต้อง
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            features = data.get('features', [])
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"Error reading history file: {e}")
        return
    
    daily_data = {}
    for f in features:
        # ป้องกันกรณีฟิลด์ properties หรือ date หายไป
        props = f.get('properties', {})
        date = props.get('date')
        
        if not date: 
            continue # ข้ามข้อมูลที่ไม่มีวันที่ชัดเจน
            
        if date not in daily_data: 
            daily_data[date] = []
        daily_data[date].append(f)
            
    summary_features = []
    for date, items in daily_data.items():
        # แก้ Logic Bug: เปลี่ยนจาก '> 0' เป็นการเช็คว่าค่าไม่ใช่ None และไม่ใช้ค่าล้างข้อมูล (-99)
        # (สมมติว่าถ้าค่าไม่มีจริงจาก API เวอร์ชันก่อนหน้า ให้ข้ามไป)
        valid_temps = [
            i for i in items 
            if i.get('properties', {}).get('temp') is not None and i['properties']['temp'] != -99.0
        ]
        
        if not valid_temps: 
            continue
        
        # หาค่า Min/Max อุณหภูมิอย่างปลอดภัย
        min_f = min(valid_temps, key=lambda x: x['properties'].get('temp', 999.0))
        max_f = max(valid_temps, key=lambda x: x['properties'].get('temp', -999.0))
        
        # หาค่าฝนสูงสุดอย่างปลอดภัย (ใช้ .get ป้องกัน KeyError และใส่ default เป็น 0.0)
        max_r24 = max(items, key=lambda x: x.get('properties', {}).get('rainfall_24hr', 0.0))
        
        # ดึงค่ามาสร้าง Feature สรุป (ใช้ .get ป้องกัน KeyError เผื่อบางฟิลด์ขาดหาย)
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
    print("Summary generated successfully!")

if __name__ == "__main__":
    generate_summary()
