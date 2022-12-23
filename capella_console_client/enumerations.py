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
    VS = "VS"
    ACD = "ACD"


class AssetType(str, BaseEnum):
    # shared
    preview = "preview"
    thumbnail = "thumbnail"
    # img product type assets
    HH = "HH"
    VV = "VV"
    raster = "raster"
    metadata = "metadata"
    # analytic produc type assets
    # VS
    analytic_product = "analytic_product"
    analytic_product_diag = "analytic_product_diag"
    landmask = "landmask"
    # ACD
    changemap = "changemap"
    # internal only
    log = "log"
    profile = "profile"
    stats = "stats"
    stats_plots = "stats_plots"


class ProductClass(str, BaseEnum):
    standard = "standard"
    extended = "extended"
    custom = "custom"


class OrbitState(str, BaseEnum):
    ascending = "ascending"
    descending = "descending"


class ObservationDirection(str, BaseEnum):
    left = "left"
    right = "right"


class OrbitalPlane(str, BaseEnum):
    fortyfive = 45
    fiftythree = 53
    ninetyseven = 97


class InstrumentMode(str, BaseEnum):
    stripmap = "stripmap"
    spotlight = "spotlight"
    sliding_spotlight = "sliding_spotlight"


class TaskingRequestStatus(str, BaseEnum):
    received = "received"
    review = "review"
    submitted = "submitted"
    active = "active"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"
    completed = "completed"
    anomaly = "anomaly"
    canceled = "canceled"
    error = "error"
    failed = "failed"
