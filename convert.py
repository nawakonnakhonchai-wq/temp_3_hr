import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import geojson
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_wind_direction_label(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((degrees + 22.5) % 360 / 45)
    return directions[index]

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
        except: history_features = []
    
    timestamp = datetime.now().isoformat()
    for f in features:
        f['properties']['record_timestamp'] = timestamp
        history_features.append(f)
    
    limit_date = datetime.now() - timedelta(days=30)
    filtered = [f for f in history_features if datetime.fromisoformat(f['properties']['record_timestamp']) > limit_date]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(filtered), f, ensure_ascii=False, indent=2)

def fetch_and_convert():
    url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    response = session.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    
    features = []
    for station in root.findall('.//Station'):
        lat = float(station.find('Latitude').text)
        lng = float(station.find('Longitude').text)
        obs = station.find('Observation')
        dt_str = obs.find('DateTime').text
        w_deg = float(obs.find('WindDirection').text) if obs.find('WindDirection') is not None else 0
        
        props = {
            "station_name": station.find('StationNameThai').text,
            "province": station.find('Province').text,
            "temp": float(obs.find('AirTemperature').text) if obs.find('AirTemperature') is not None else 0,
            "rainfall": float(obs.find('Rainfall').text) if obs.find('Rainfall') is not None else 0,
            "rainfall_24hr": float(obs.find('Rainfall24Hr').text) if obs.find('Rainfall24Hr') is not None else 0,
            "wind_speed": float(obs.find('WindSpeed').text) if obs.find('WindSpeed') is not None else 0,
            "wind_direction_deg": w_deg,
            "wind_direction_label": get_wind_direction_label(w_deg),
            "date": dt_str.split(' ')[0],
            "time": dt_str.split(' ')[1]
        }
        features.append(geojson.Feature(geometry=geojson.Point((lng, lat)), properties=props))
    
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(features), f, ensure_ascii=False, indent=2)
    save_history(features)

if __name__ == "__main__":
    fetch_and_convert()
