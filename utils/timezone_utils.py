from datetime import datetime
import pytz
from flask import session

# Common timezones for the dropdown
COMMON_TIMEZONES = [
    ('UTC', 'UTC (Coordinated Universal Time)'),
    ('US/Eastern', 'US Eastern Time'),
    ('US/Central', 'US Central Time'),
    ('US/Mountain', 'US Mountain Time'),
    ('US/Pacific', 'US Pacific Time'),
    ('Europe/London', 'London (GMT/BST)'),
    ('Europe/Paris', 'Paris (CET/CEST)'),
    ('Europe/Berlin', 'Berlin (CET/CEST)'),
    ('Europe/Rome', 'Rome (CET/CEST)'),
    ('Europe/Madrid', 'Madrid (CET/CEST)'),
    ('Europe/Amsterdam', 'Amsterdam (CET/CEST)'),
    ('Europe/Prague', 'Prague (CET/CEST)'),
    ('Europe/Bratislava', 'Bratislava (CET/CEST)'),
    ('Europe/Vienna', 'Vienna (CET/CEST)'),
    ('Europe/Zurich', 'Zurich (CET/CEST)'),
    ('Europe/Moscow', 'Moscow (MSK)'),
    ('Asia/Tokyo', 'Tokyo (JST)'),
    ('Asia/Shanghai', 'Shanghai (CST)'),
    ('Asia/Kolkata', 'India (IST)'),
    ('Asia/Dubai', 'Dubai (GST)'),
    ('Australia/Sydney', 'Sydney (AEDT/AEST)'),
    ('Australia/Melbourne', 'Melbourne (AEDT/AEST)'),
    ('Pacific/Auckland', 'Auckland (NZDT/NZST)'),
]

def convert_utc_to_user_timezone(utc_datetime, user_timezone='UTC'):
    """Convert UTC datetime to user's timezone"""
    if not utc_datetime:
        return None
    
    # If datetime is naive, assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    
    # Convert to user's timezone
    user_tz = pytz.timezone(user_timezone)
    return utc_datetime.astimezone(user_tz)

def format_datetime_for_user(utc_datetime, user_timezone='UTC', format_string='%B %d, %Y at %I:%M %p'):
    """Format datetime for user's timezone"""
    if not utc_datetime:
        return "Not available"
    
    user_datetime = convert_utc_to_user_timezone(utc_datetime, user_timezone)
    return user_datetime.strftime(format_string)

def get_user_timezone():
    """Get user timezone from session or default to UTC"""
    return session.get('user_timezone', 'UTC')

def set_user_timezone(timezone):
    """Set user timezone in session"""
    session['user_timezone'] = timezone
