from datetime import datetime, timedelta
import pytz


def test_tz():
    print(
        (datetime.now(pytz.timezone("America/Denver")) + timedelta(days=1)).replace(
            hour=7, minute=0, second=0, microsecond=0
        )
    )
