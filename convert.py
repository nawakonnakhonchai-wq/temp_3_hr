import requests
import geojson
import xml.etree.ElementTree as ET

def fetch_and_convert_tmd_data(url):
    # 1. ดึงข้อมูลจาก API
    response = requests.get(url)
    root = ET.fromstring(response.content)
    
    features = []
    
    # 2. วนลูปในแต่ละ <Station>
    for station in root.findall('.//Station'):
        lat = float(station.find('Latitude').text)
        lng = float(station.find('Longitude').text)
        
        # ดึงข้อมูลจาก <Observation>
        obs = station.find('Observation')
        
        # สร้าง Feature (จุดบนแผนที่)
        point = geojson.Point((lng, lat))
        feature = geojson.Feature(geometry=point, properties={
            "station_id": station.find('WmoStationNumber').text,
            "name_th": station.find('StationNameThai').text,
            "province": station.find('Province').text,
            "temperature": float(obs.find('AirTemperature').text),
            "humidity": float(obs.find('RelativeHumidity').text),
            "wind_speed": float(obs.find('WindSpeed').text),
            "rainfall": float(obs.find('Rainfall').text),
            "datetime": obs.find('DateTime').text
        })
        features.append(feature)
    
    # 3. รวมเป็น FeatureCollection
    return geojson.FeatureCollection(features)

# เรียกใช้งาน
url = 'http://data.tmd.go.th/api/Weather3Hours/V2/index.php'
collection = fetch_and_convert_tmd_data(url)

with open('weather_data.geojson', 'w', encoding='utf-8') as f:
    geojson.dump(collection, f, indent=2)
