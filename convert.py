import requests
import geojson
import xml.etree.ElementTree as ET

def fetch_and_convert_tmd_data(url):
    # เพิ่ม Headers เพื่อเลียนแบบ Browser ปกติป้องกันการโดนบล็อก
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # ตรวจสอบว่าดึงข้อมูลสำเร็จหรือไม่
        
        # ถอดรหัส XML (ต้องระวังเรื่อง Encoding ของไทย)
        root = ET.fromstring(response.content)
        
        features = []
        for station in root.findall('.//Station'):
            # ดึง Lat/Long พร้อมจัดการกรณีไม่มีข้อมูล
            lat_node = station.find('Latitude')
            lng_node = station.find('Longitude')
            
            if lat_node is not None and lng_node is not None:
                lat = float(lat_node.text)
                lng = float(lng_node.text)
                
                obs = station.find('Observation')
                
                # สร้าง Feature
                point = geojson.Point((lng, lat))
                feature = geojson.Feature(geometry=point, properties={
                    "station_name": station.find('StationNameThai').text,
                    "province": station.find('Province').text,
                    "temp": float(obs.find('AirTemperature').text) if obs.find('AirTemperature') is not None else 0,
                    "humidity": float(obs.find('RelativeHumidity').text) if obs.find('RelativeHumidity') is not None else 0,
                    "wind": float(obs.find('WindSpeed').text) if obs.find('WindSpeed') is not None else 0
                })
                features.append(feature)
        
        return geojson.FeatureCollection(features)
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# เรียกใช้งาน
url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
collection = fetch_and_convert_tmd_data(url)

if collection:
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(collection, f, ensure_ascii=False, indent=2)
    print("Successfully created weather_data.geojson")
