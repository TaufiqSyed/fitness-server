from datetime import datetime, timezone
import pytz

def get_current_day():
    timezone = pytz.timezone('Asia/Dubai')
    return int(datetime.now(timezone).strftime('%w'))