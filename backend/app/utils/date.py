from datetime import datetime

import pytz

datetime_format = "%b %d %Y %I:%M:%S %p"


def formated_date():
    kathmandu_tz = pytz.timezone("Asia/Kathmandu")
    return datetime.now(kathmandu_tz).strftime(datetime_format)