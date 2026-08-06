import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from src.config import Config
from src.database import DatabaseManager
from src.parser import DataParser

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.db = DatabaseManager()
        self.parser = DataParser()
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """สร้าง Session สำหรับ requests"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'application/json, text/html, application/xhtml+xml, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_station_data(self, station: str) -> Optional[Dict]:
        """
        ดึงข้อมูลของสถานีเดียว
        รองรับทั้ง JSON และ HTML
        """
        try:
            # ลองเรียก API แบบ JSON ก่อน
            api_url = f"{Config.BASE_URL}{Config.API_ENDPOINT}"
            params = {'station': station, 'format': 'json'}
            
            response = self.session.get(
                api_url,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    data = self.parser.parse_json(response.json(), station)
                    if data:
                        data['datetime'] = datetime.now().isoformat()
                        self.db.log_fetch(station, True)
                        return data
                
                # ถ้าไม่ใช่ JSON หรือ parse ไม่ได้ ลองแบบ HTML
                html_data = self.parser.parse_html(response.text, station)
                if html_data:
                    html_data['datetime'] = datetime.now().isoformat()
                    self.db.log_fetch(station, True)
                    return html_data
            
            # ถ้า API ไม่ได้ผล ลองเรียก HTML โดยตรง
            html_url = f"{Config.BASE_URL}{Config.HTML_ENDPOINT}"
            response = self.session.get(
                html_url,
                params={'station': station},
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = self.parser.parse_html(response.text, station)
                if data:
                    data['datetime'] = datetime.now().isoformat()
                    self.db.log_fetch(station, True)
                    return data
            
            # ถ้ายังไม่ได้ข้อมูล
            logger.warning(f"No data found for station {station}")
            self.db.log_fetch(station, False, "No data found")
            return None
            
        except requests.Timeout:
            error_msg = f"Timeout fetching {station}"
            logger.error(error_msg)
            self.db.log_fetch(station, False, error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Error fetching {station}: {str(e)}"
            logger.error(error_msg)
            self.db.log_fetch(station, False, error_msg)
            return None
    
    def fetch_all_stations(self) -> List[Dict]:
        """ดึงข้อมูลทุกสถานีพร้อมกัน"""
        all_data = []
        logger.info(f"Starting fetch for {len(Config.STATIONS)} stations")
        
        for station in Config.STATIONS:
            logger.info(f"Fetching {station}...")
            
            data = self.fetch_station_data(station)
            if data:
                all_data.append(data)
                logger.info(f"✅ {station}: {data['level']:.2f} m ({data['status']})")
            else:
                logger.warning(f"❌ {station}: Failed to fetch")
            
            # หน่วงเวลาเล็กน้อยเพื่อป้องกันการบล็อค
            time.sleep(0.5)
        
        # บันทึกข้อมูล
        if all_data:
            saved = self.db.save_data(all_data)
            logger.info(f"💾 Saved {saved} records to database")
        else:
            logger.warning("No data to save")
        
        return all_data
    
    def fetch_with_retry(self, station: str, max_retries: int = 3) -> Optional[Dict]:
        """ดึงข้อมูลพร้อมระบบ retry"""
        for attempt in range(max_retries):
            try:
                data = self.fetch_station_data(station)
                if data:
                    return data
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retry {attempt + 1}/{max_retries} for {station} in {wait_time}s")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Retry {attempt + 1} error for {station}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None
    
    def run_once(self):
        """รันการดึงข้อมูลหนึ่งครั้ง"""
        logger.info("="*50)
        logger.info(f"Starting fetch job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
        
        data = self.fetch_all_stations()
        
        # ตรวจสอบการแจ้งเตือน
        if data:
            from src.notifier import Notifier
            notifier = Notifier()
            notifier.check_and_notify(data)
        
        logger.info("="*50)
        logger.info(f"Job completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
