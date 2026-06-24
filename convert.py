import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import geojson

# 1. ฟังก์ชันช่วยคำนวณทิศทางลม
def get_wind_direction_label(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((degrees + 22.5) % 360 / 45)
    return directions[index]

# 2. ฟังก์ชันจัดการประวัติศาสตร์ย้อนหลัง 30 วัน
def save_history(features):
    history_dir = 'history'
    os.makedirs(history_dir, exist_ok=True)
    history_file = f"{history_dir}/weather_history.json"
    
    # โหลดประวัติเดิม
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
            
    # เพิ่มข้อมูลใหม่
    entry = {
        "timestamp": datetime.now().isoformat(),
        "features": features
    }
    history.append(entry)
    
    # กรองเอาเฉพาะข้อมูลไม่เกิน 30 วันย้อนหลัง
    limit_date = datetime.now() - timedelta(days=30)
    filtered_history = [h for h in history if datetime.fromisoformat(h['timestamp']) > limit_date]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_history, f, ensure_ascii=False, indent=2)

# 3. ฟังก์ชันหลักในการดึงข้อมูล
def fetch_and_convert():
    url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    
    features = []
    for station in root.findall('.//Station'):
        lat = float(station.find('Latitude').text)
        lng = float(station.find('Longitude').text)
        obs = station.find('Observation')
        
        # ดึงค่าข้อมูล
        dt_str = obs.find('DateTime').text
        w_deg = float(obs.find('WindDirection').text) if obs.find('WindDirection') is not None else 0
        
        # เก็บข้อมูลลงใน Properties
        props = {
            "station_name": station.find('StationNameThai').text,
            "province": station.find('Province').text,
            "temp": float(obs.find('AirTemperature').text) if obs.find('AirTemperature') is not None else 0,
            "humidity": float(obs.find('RelativeHumidity').text) if obs.find('RelativeHumidity') is not None else 0,
            "wind_speed": float(obs.find('WindSpeed').text) if obs.find('WindSpeed') is not None else 0,
            "wind_direction_deg": w_deg,
            "wind_direction_label": get_wind_direction_label(w_deg),
            "wind_direction_to": (w_deg + 180) % 360,
            "rainfall": float(obs.find('Rainfall').text) if obs.find('Rainfall') is not None else 0,
            "rainfall_24hr": float(obs.find('Rainfall24Hr').text) if obs.find('Rainfall24Hr') is not None else 0,
            "date": dt_str.split(' ')[0],
            "time": dt_str.split(' ')[1],
            "full_datetime": dt_str
        }
        features.append(geojson.Feature(geometry=geojson.Point((lng, lat)), properties=props))
    
    # สร้าง FeatureCollection
    collection = geojson.FeatureCollection(features)
    
    # บันทึกไฟล์ปัจจุบัน
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(collection, f, ensure_ascii=False, indent=2)
        
    # บันทึกประวัติ
    save_history([f.properties for f in features])

if __name__ == "__main__":
    fetch_and_convert()
