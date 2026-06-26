import os, json, requests, geojson, copy, xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- ฟังก์ชันช่วย (Helper Functions) ---
def get_wind_direction_label(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[int((float(degrees) + 22.5) % 360 / 45) % 8]

def safe_find_text(element, path, default=""):
    target = element.find(path)
    return target.text.strip() if target is not None and target.text else default

def safe_float(element, path, default=0.0):
    try: return float(safe_find_text(element, path, default))
    except: return default

# --- ฟังก์ชันหลัก ---
def fetch_and_convert():
    url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=5)))
    
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    features = []
    timestamp = datetime.now().isoformat()
    
    for station in root.findall('.//Station'):
        obs = station.find('Observation')
        if obs is None: continue
        
        lat = safe_float(station, 'Latitude')
        lng = safe_float(station, 'Longitude')
        w_deg = safe_float(obs, 'WindDirection')
        
        props = {
            "station_name": safe_find_text(station, 'StationNameThai'),
            "province": safe_find_text(station, 'Province'),
            "temp": safe_float(obs, 'AirTemperature'),
            "rainfall": safe_float(obs, 'Rainfall'),
            "rainfall_24hr": safe_float(obs, 'Rainfall24Hr'),
            "wind_speed": safe_float(obs, 'WindSpeed'),
            "wind_direction_deg": w_deg,
            "wind_direction_label": get_wind_direction_label(w_deg),
            "date": safe_find_text(obs, 'DateTime').split(' ')[0],
            "record_timestamp": timestamp
        }
        features.append(geojson.Feature(geometry=geojson.Point((lng, lat)), properties=props))

    # 1. เขียนไฟล์ปัจจุบัน
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(features), f, ensure_ascii=False, indent=2)

    # 2. อัปเดต History (30 วัน)
    history_dir = 'history'
    os.makedirs(history_dir, exist_ok=True)
    history_file = f"{history_dir}/weather_history.geojson"
    
    history_features = []
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            try: history_features = json.load(f).get('features', [])
            except: pass
    
    # รวมของใหม่เข้าไป
    history_features.extend(copy.deepcopy(features))
    
    # กรองเอาเฉพาะ 30 วันล่าสุด
    limit_date = datetime.now() - timedelta(days=30)
    filtered = [f for f in history_features if datetime.fromisoformat(f['properties'].get('record_timestamp', '2000-01-01')) > limit_date]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(filtered), f, ensure_ascii=False, indent=2)
    print("Fetch and Convert success!")

if __name__ == "__main__":
    fetch_and_convert()
