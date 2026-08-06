import logging
from typing import List, Dict
from src.config import Config

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        self.thresholds = Config.ALERT_THRESHOLDS
    
    def check_and_notify(self, data_list: List[Dict]):
        """ตรวจสอบและแจ้งเตือน"""
        alerts = []
        
        for data in data_list:
            station = data['station']
            level = data['level']
            
            if station in self.thresholds:
                thresholds = self.thresholds[station]
                
                if level >= thresholds.get('critical', float('inf')):
                    alerts.append({
                        'level': 'critical',
                        'message': f"🔴 วิกฤต! สถานี {station} ระดับน้ำ {level:.2f} ม. (เกินเกณฑ์วิกฤต {thresholds['critical']} ม.)"
                    })
                elif level >= thresholds.get('danger', float('inf')):
                    alerts.append({
                        'level': 'danger',
                        'message': f"⚠️ อันตราย! สถานี {station} ระดับน้ำ {level:.2f} ม. (เกินเกณฑ์อันตราย {thresholds['danger']} ม.)"
                    })
                elif level >= thresholds.get('warning', float('inf')):
                    alerts.append({
                        'level': 'warning',
                        'message': f"🔶 เฝ้าระวัง! สถานี {station} ระดับน้ำ {level:.2f} ม. (เกินเกณฑ์เฝ้าระวัง {thresholds['warning']} ม.)"
                    })
        
        if alerts:
            for alert in alerts:
                logger.warning(f"🚨 ALERT: {alert['message']}")
            
            # ส่ง Line Notify
            if Config.LINE_NOTIFY_ENABLED and Config.LINE_NOTIFY_TOKEN:
                self.send_line_notify(alerts)
        
        return alerts
    
    def send_line_notify(self, alerts: List[Dict]):
        """ส่งข้อความผ่าน Line Notify"""
        try:
            import requests
            
            messages = ["📊 *รายงานสถานการณ์น้ำ*"]
            messages.append(f"🕐 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            messages.append("")
            
            for alert in alerts:
                messages.append(alert['message'])
            
            message = "\n".join(messages)
            
            response = requests.post(
                'https://notify-api.line.me/api/notify',
                headers={
                    'Authorization': f'Bearer {Config.LINE_NOTIFY_TOKEN}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={'message': message},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Line notification sent successfully")
            else:
                logger.error(f"❌ Failed to send Line notification: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error sending Line notification: {e}")
