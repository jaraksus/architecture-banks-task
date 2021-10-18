from datetime import datetime, timedelta


class ITimeManager(object):
    def get_datetime(self):
        raise NotImplementedError("get_datetime must be implemented")


class TToyTimeManager(ITimeManager):
    def __init__(self, start_datetime: datetime, step: timedelta):
        self.datetime = start_datetime
        self.step = step

    def get_datetime(self):
        return self.datetime
    
    def next(self):
        self.datetime += self.step
