from datetime import datetime


class TimestampConverter:
    @staticmethod
    def from_string(timestamp):
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
