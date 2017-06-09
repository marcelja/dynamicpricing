import json

class PricewarsObject:

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_list(cls, l):
        return [cls.from_dict(e) for e in l]
