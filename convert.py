import requests
import geojson
import xml.etree.ElementTree as ET

def get_wind_direction_label(degrees):
    """แปลงองศาเป็นตัวอักษรทิศ"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((degrees + 22.5) % 360 / 45)
    return directions[index]

def fetch_and_convert_tmd_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        features = []
        
        for station in root.findall('.//Station'):
            lat_node = station.find('Latitude')
            lng_node = station.find('Longitude')
            
            if lat_node is not None and lng_node is not None:
                lat = float(lat_node.text)
                lng = float(lng_node.text)
                obs = station.find('Observation')
                
                # ดึงค่าตัวเลขเพื่อคำนวณ
                w_deg = float(obs.find('WindDirection').text) if obs.find('WindDirection') is not None else 0
                
                # คำนวณทิศที่ลมพัดไป (บวก 180 องศา)
                w_to = (w_deg + 180) % 360
                
                point = geojson.Point((lng, lat))
                feature = geojson.Feature(geometry=point, properties={
                    "station_name": station.find('StationNameThai').text,
                    "province": station.find('Province').text,
                    "temp": float(obs.find('AirTemperature').text) if obs.find('AirTemperature') is not None else 0,
                    "humidity": float(obs.find('RelativeHumidity').text) if obs.find('RelativeHumidity') is not None else 0,
                    "wind_speed": float(obs.find('WindSpeed').text) if obs.find('WindSpeed') is not None else 0,
                    "wind_direction_deg": w_deg,
                    "wind_direction_label": get_wind_direction_label(w_deg),
                    "wind_direction_to": w_to,
                    "rainfall": float(obs.find('Rainfall').text) if obs.find('Rainfall') is not None else 0,
                    "rainfall_24hr": float(obs.find('Rainfall24Hr').text) if obs.find('Rainfall24Hr') is not None else 0,
                    "datetime": obs.find('DateTime').text if obs.find('DateTime') is not None else ""
                })
                features.append(feature)
        
        return geojson.FeatureCollection(features)
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# URL ของ TMD
url = 'https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345'
collection = fetch_and_convert_tmd_data(url)

if collection:
    with open('weather_data.geojson', 'w', encoding='utf-8') as f:
        geojson.dump(collection, f, ensure_ascii=False, indent=2)
    print("Successfully created weather_data.geojson with all fields")
