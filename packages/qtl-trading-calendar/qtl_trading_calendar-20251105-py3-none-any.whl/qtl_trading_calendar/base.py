from datetime import date, datetime, timedelta

from .utils import is_weekend


class BaseTradingCalendar:
    def __init__(self):
        self.config = None
        self.init_config()

    def ensure_date(self, d):
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, date):
            return d
        raise TypeError(f'Invalid date type: {type(d)}')

    def check_date(self, d: date):
        if not (self.start_date <= d <= self.end_date):
            raise AttributeError('Out of Calendar Date Range...')

    def has_day_trading(self, d: date):
        d = self.ensure_date(d)
        self.check_date(d)
        if is_weekend(d):
            return False
        if d in self.no_day_trading_dates:
            return False
        return True

    def has_night_trading(self, d: date):
        d = self.ensure_date(d)
        self.check_date(d)
        if is_weekend(d):
            return False
        if d in self.no_night_trading_dates:
            return False
        return True

    def is_trading_day(self, d: date):
        return self.has_day_trading(d) or self.has_night_trading(d)

    def current_trading_day(self):
        now = datetime.now()
        return self.get_trading_day(now)

    def next_trading_day(self, d: date, n=1):
        d = self.ensure_date(d)
        count = 0
        while True:
            d = d + timedelta(days=1)
            if self.is_trading_day(d):
                count += 1
                if count >= n:
                    return d

    def previous_trading_day(self, d: date, n=1):
        d = self.ensure_date(d)
        count = 0
        while True:
            d = d - timedelta(days=1)
            if self.is_trading_day(d):
                count += 1
                if count >= n:
                    return d
