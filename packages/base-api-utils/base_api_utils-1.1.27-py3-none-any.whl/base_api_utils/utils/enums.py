from enum import Enum


class EnumChoices(Enum):

    @classmethod
    def choices(cls):
        return [(item.value, item.name.replace('_', ' ').title()) for item in cls]