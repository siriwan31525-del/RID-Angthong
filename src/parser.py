import re
import json
from typing import Optional, Dict
from bs4 import BeautifulSoup
import pandas as pd

class DataParser:
    """จัดการการแยกวิเคราะห์ข้อมูลจาก HTML และ JSON"""
    
    @staticmethod
    def parse_html(html_content: str, station: str) -> Optional[Dict]:
        """แยกวิเคราะห์ข้อมูลจาก HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # ตัวอย่างการหา element (ต้องปรับตามโครงสร้างจริง)
            # 1. หาค่าระดับน้ำ
            level = None
            level_patterns = [
                ('span', 'water-level'),
                ('div', 'level'),
                ('td', 'water'),
                ('span', 'value'),
                ('div', 'data-value')
            ]
            
            for tag, class_name in level_patterns:
                element = soup.find(tag, class_=class_name)
                if element:
                    text = element.text.strip()
                    # ดึงตัวเลขจากข้อความ
                    numbers = re.findall(r'[\d.]+', text)
                    if numbers:
                        level = float(numbers[0])
                        break
            
            # 2. หาสถานะ
            status = 'ปกติ'
            status_patterns = [
                ('span', 'status'),
                ('div', 'condition'),
                ('td', 'status')
            ]
            
            for tag, class_name in status_patterns:
                element = soup.find(tag, class_=class_name)
                if element:
                    status_text = element.text.strip()
                    if 'วิกฤต' in status_text or 'อันตราย' in status_text:
                        status = 'วิกฤต'
                    elif 'เฝ้าระวัง' in status_text or 'สูง' in status_text:
                        status = 'เฝ้าระวัง'
                    else:
                        status = 'ปกติ'
                    break
            
            # ถ้ายังหาค่าไม่ได้ ลองค้นหาจากตาราง
            if level is None:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            text = cell.text.strip()
                            if station in text:
                                # หาค่าในเซลล์ถัดไป
                                next_cell = cell.find_next('td')
                                if next_cell:
                                    numbers = re.findall(r'[\d.]+', next_cell.text)
                                    if numbers:
                                        level = float(numbers[0])
                                        break
            
            if level is not None:
                return {
                    'station': station,
                    'level': level,
                    'status': status,
                    'raw_data': html_content[:1000]  # เก็บส่วนหนึ่ง
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing HTML for {station}: {e}")
            return None
    
    @staticmethod
    def parse_json(json_data: str, station: str) -> Optional[Dict]:
        """แยกวิเคราะห์ข้อมูลจาก JSON"""
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # พยายามหา key ที่น่าจะมีค่าระดับน้ำ
            level_keys = ['level', 'waterLevel', 'water_level', 'value', 'data']
            status_keys = ['status', 'condition', 'state']
            
            level = None
            status = 'ปกติ'
            
            # ค้นหาใน JSON แบบ recursive
            def find_value(obj, keys):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() in keys:
                            return value
                        if isinstance(value, (dict, list)):
                            result = find_value(value, keys)
                            if result is not None:
                                return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_value(item, keys)
                        if result is not None:
                            return result
                return None
            
            level = find_value(data, level_keys)
            status_text = find_value(data, status_keys)
            
            if level is not None:
                try:
                    level = float(level)
                except (ValueError, TypeError):
                    # ถ้าแปลงเป็น float ไม่ได้ ลองหาค่าตัวเลข
                    if isinstance(level, str):
                        numbers = re.findall(r'[\d.]+', level)
                        if numbers:
                            level = float(numbers[0])
                        else:
                            level = None
            
            if status_text:
                if isinstance(status_text, str):
                    if 'วิกฤต' in status_text or 'อันตราย' in status_text:
                        status = 'วิกฤต'
                    elif 'เฝ้าระวัง' in status_text or 'สูง' in status_text:
                        status = 'เฝ้าระวัง'
            
            if level is not None:
                return {
                    'station': station,
                    'level': level,
                    'status': status,
                    'raw_data': json.dumps(data)[:1000]
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing JSON for {station}: {e}")
            return None
    
    @staticmethod
    def detect_format(content: str) -> str:
        """ตรวจจับรูปแบบข้อมูล"""
        # ตรวจสอบว่าเป็น JSON
        try:
            json.loads(content)
            return 'json'
        except:
            pass
        
        # ตรวจสอบว่าเป็น HTML
        if '<html' in content.lower() or '<body' in content.lower():
            return 'html'
        
        # ตรวจสอบว่าเป็น XML
        if '<?xml' in content:
            return 'xml'
        
        return 'unknown'
