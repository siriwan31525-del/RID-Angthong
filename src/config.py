import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    
    # Database
    DB_PATH = os.getenv('DB_PATH', str(DATA_DIR / 'water_data.db'))
    
    # Website URLs
    BASE_URL = os.getenv('BASE_URL', 'https://hyd-app.rid.go.th')
    API_ENDPOINT = os.getenv('STATION_API_ENDPOINT', '/api/station')
    HTML_ENDPOINT = os.getenv('HTML_ENDPOINT', '/hydro5h.html')
    
    # Stations to track
    STATIONS = ['C.46', 'C.7A', 'C.47']
    
    # Fetch configuration
    FETCH_INTERVAL_MINUTES = int(os.getenv('FETCH_INTERVAL_MINUTES', 1))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
    USER_AGENT = os.getenv('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Alert thresholds (meters)
    ALERT_THRESHOLDS = {
        'C.46': {'warning': 2.5, 'danger': 3.0, 'critical': 3.5},
        'C.7A': {'warning': 3.0, 'danger': 3.5, 'critical': 4.0},
        'C.47': {'warning': 2.8, 'danger': 3.2, 'critical': 3.8}
    }
    
    # Notification settings
    LINE_NOTIFY_TOKEN = os.getenv('LINE_NOTIFY_TOKEN', '')
    LINE_NOTIFY_ENABLED = os.getenv('LINE_NOTIFY_ENABLED', 'false').lower() == 'true'
    
    # Dashboard
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8501))
    DASHBOARD_TITLE = os.getenv('DASHBOARD_TITLE', '🌊 ระบบติดตามสถานการณ์น้ำ')
    
    # Create data directory if not exists
    DATA_DIR.mkdir(exist_ok=True)
