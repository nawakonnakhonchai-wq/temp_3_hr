import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import geojson
import copy  # เพิ่มเพื่อแก้ปัญหา Object Reference
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_wind_direction_label(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    # ใช้ % 8 เพื่อการันตีว่า index จะอยู่แค่ 0-7 เสมอ ป้องกัน IndexError
    index = int((degrees + 22.5) % 360 / 45) % 8
    return directions[index]

# ฟังก์ชันช่วยดึงค่าข้อความแบบปลอดภัย
def safe_find_text(element, path, default=""):
    target = element.find(path)
    if target is not None and target.text is not None:
        return target.text.strip()
    return default

# ฟังก์ชันช่วยแปลงเลขแบบปลอดภัย
def safe_float(element, path, default=0.0):
    text = safe_find_text(element, path)
    try:
        return float(text)
    except ValueError:
        return default

def save_history(features):
    history_dir = 'history'
    os.makedirs(history_dir, exist_ok=True)
    history_file = f"{history_dir}/weather_history.geojson"
    
    history_features = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                history_features = data.get('features', [])
        except json.JSONDecodeError:
            # หากไฟล์พัง แนะนำให้ Rename ไฟล์เก่าทิ้งไว้เพื่อกู้ข้อมูล แทนที่จะปล่อยให้หายไปเฉยๆ
            print(f"Warning: {history_file} is corrupted. Creating a new one.")
            history_features = []
    
    timestamp = datetime.now().isoformat()
    for f in features:
        # ใช้ copy.deepcopy เพื่อไม่ให้กระทบกับข้อมูลใน weather_data.geojson
        f_copy = copy.deepcopy(f)
        f_copy['properties']['record_timestamp'] = timestamp
        history_features.append(f_copy)
    
    limit_date = datetime.now() - timedelta(days=30)
    
    filtered = []
    for f in history_features:
        try:
            ts_str = f.get('properties', {}).get('record_timestamp', '')
            if datetime.fromisoformat(ts_str) > limit_date:
                filtered.append(f)
        except (ValueError, TypeError):
            # ข้ามกรณีที่ format วันที่ในประวัติเสียหาย เพื่อไม่ให้โปรแกรมหยุดทำงาน
            continue
    
    with open(history_file, 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(filtered), f, ensure_ascii=False, indent=2)

def fetch_and_convert():
    url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    try:
        response = session.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"Network or XML Parsing Error: {e}")
        return
    
    features = []
    for station in root.findall('.//Station'):
        lat = safe_float(station, 'Latitude', 0.0)
        lng = safe_float(station, 'Longitude', 0.0)
        
        obs = station.find('Observation')
        if obs is None:
            continue  # ถ้าไม่มีข้อมูลตรวจวัดเลยให้ข้ามสถานีนี้ไป
            
        dt_str = safe_find_text(obs, 'DateTime')
        
        # จัดการแยกวันที่และเวลาให้ปลอดภัยขึ้น รองรับทั้ง Space และ 'T' (ISO format)
        if 'T' in dt_str:
            date_part, time_part = dt_str.split('T')
        elif ' ' in dt_str:
            parts = dt_str.split(' ')
            date_part, time_part = parts[0], parts[1]
        else:
            date_part, time_part = dt_str, ""

        w_deg = safe_float(obs, 'WindDirection', 0.0)
        
        props = {
            "station_name": safe_find_text(station, 'StationNameThai'),
            "province": safe_find_text(station, 'Province'),
            "temp": safe_float(obs, 'AirTemperature', 0.0),
            "rainfall": safe_float(obs, 'Rainfall', 0.0),
            "rainfall_24hr": safe_float(obs, 'Rainfall24Hr', 0.0),
            "wind_speed": safe_float(obs, 'WindSpeed', 0.0),
            "wind_direction_deg": w_deg,
            "wind_direction_label": get_wind_direction_label(w_deg),
            "date": date_part,
            "time": time_part
        }
        features.append(geojson.Feature(geometry=geojson.Point((lng, lat)), properties=props))
    
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(features), f, ensure_ascii=False, indent=2)
    
    save_history(features)

if __name__ == "__main__":
    fetch_and_convert()
