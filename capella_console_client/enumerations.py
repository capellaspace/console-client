from enum import Enum, EnumMeta


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


class ProductType(str, BaseEnum):
    SLC = "SLC"
    GEO = "GEO"
    SICD = "SICD"
    GEC = "GEC"
    SIDD = "SIDD"
    CPHD = "CPHD"
