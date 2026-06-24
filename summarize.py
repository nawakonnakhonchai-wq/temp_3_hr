import json
import os

def generate_summary():
    # ตรวจสอบว่ามีโฟลเดอร์ stats หรือไม่ ถ้าไม่มีให้สร้าง
    os.makedirs('stats', exist_ok=True)
    history_file = 'history/weather_history.json'
    
    if not os.path.exists(history_file):
        print("History file not found, skipping summary.")
        return

    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    # 1. จัดกลุ่มข้อมูลตามวันที่
    daily_data = {}
    for entry in history:
        # ดึงวันที่จากข้อมูล (ใช้วันที่ของรายการนั้นๆ)
        # เนื่องจากข้อมูลใน history เก็บเป็น timestamp ของการรัน ให้ยึดตาม 'date' ใน properties
        for feature_props in entry['features']:
            date_key = feature_props['date']
            if date_key not in daily_data:
                daily_data[date_key] = {"temps": [], "rainfalls": []}
            
            daily_data[date_key]['temps'].append(feature_props['temp'])
            daily_data[date_key]['rainfalls'].append(feature_props['rainfall'])
            
    # 2. คำนวณค่า Min/Max
    stats = {}
    for date, val in daily_data.items():
        # กรองเอาเฉพาะตัวเลขที่เป็นไปได้ (ป้องกันกรณีค่าเป็น 0 ที่ผิดปกติ)
        temps = [t for t in val['temps'] if t > 0]
        
        stats[date] = {
            "min_temp": min(temps) if temps else 0,
            "max_temp": max(temps) if temps else 0,
            "total_rainfall": sum(val['rainfalls']),
            "max_rainfall": max(val['rainfalls'])
        }
        
    # 3. บันทึกไฟล์
    with open('stats/daily_summary.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("Successfully generated stats/daily_summary.json")

if __name__ == "__main__":
    generate_summary()
