import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager
from src.config import Config

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager สำหรับ connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """สร้างฐานข้อมูลและตาราง"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # ตารางหลัก
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS water_level (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    level REAL,
                    status TEXT,
                    raw_data TEXT,
                    fetch_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ตารางสำหรับ log การดึงข้อมูล
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fetch_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fetch_time TEXT NOT NULL,
                    station TEXT,
                    success INTEGER,
                    error_message TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_station_datetime 
                ON water_level(station, datetime DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_fetch_time 
                ON fetch_logs(fetch_time DESC)
            ''')
            
            conn.commit()
    
    def save_data(self, data_list: List[Dict]) -> int:
        """บันทึกข้อมูล"""
        if not data_list:
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                cursor.execute('''
                    INSERT INTO water_level 
                    (station, datetime, level, status, raw_data) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    data['station'],
                    data['datetime'],
                    data['level'],
                    data.get('status', ''),
                    data.get('raw_data', '')
                ))
            
            conn.commit()
            return len(data_list)
    
    def log_fetch(self, station: str, success: bool, error: Optional[str] = None):
        """บันทึก log การดึงข้อมูล"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO fetch_logs (fetch_time, station, success, error_message)
                VALUES (datetime('now'), ?, ?, ?)
            ''', (station, 1 if success else 0, error))
            conn.commit()
    
    def get_latest_data(self, station: Optional[str] = None) -> pd.DataFrame:
        """ดึงข้อมูลล่าสุด"""
        with self.get_connection() as conn:
            if station:
                query = '''
                    SELECT station, datetime, level, status 
                    FROM water_level 
                    WHERE station = ? 
                    ORDER BY datetime DESC 
                    LIMIT 1
                '''
                df = pd.read_sql(query, conn, params=(station,))
            else:
                query = '''
                    SELECT station, datetime, level, status 
                    FROM water_level 
                    WHERE (station, datetime) IN (
                        SELECT station, MAX(datetime) 
                        FROM water_level 
                        GROUP BY station
                    )
                    ORDER BY station
                '''
                df = pd.read_sql(query, conn)
            
            return df
    
    def get_history(self, station: Optional[str] = None, hours: int = 24) -> pd.DataFrame:
        """ดึงข้อมูลย้อนหลัง"""
        with self.get_connection() as conn:
            query = '''
                SELECT station, datetime, level 
                FROM water_level 
                WHERE datetime >= datetime('now', '-' || ? || ' hours')
            '''
            params = [hours]
            
            if station:
                query += " AND station = ?"
                params.append(station)
            
            query += " ORDER BY datetime"
            
            df = pd.read_sql(query, conn, params=params)
            return df
    
    def get_statistics(self, station: Optional[str] = None, hours: int = 24) -> Dict:
        """คำนวณสถิติ"""
        df = self.get_history(station, hours)
        if df.empty:
            return {}
        
        stats = df.groupby('station')['level'].agg([
            ('count', 'count'),
            ('mean', 'mean'),
            ('max', 'max'),
            ('min', 'min'),
            ('std', 'std')
        ]).to_dict('index')
        
        return stats
    
    def get_all_stations(self) -> List[str]:
        """ดึงรายชื่อสถานีทั้งหมด"""
        with self.get_connection() as conn:
            df = pd.read_sql("SELECT DISTINCT station FROM water_level ORDER BY station", conn)
            return df['station'].tolist()
    
    def cleanup_old_data(self, days: int = 30):
        """ลบข้อมูลเก่า"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM water_level 
                WHERE datetime < datetime('now', '-' || ? || ' days')
            ''', (days,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
