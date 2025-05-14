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
    CSI = "CSI"
    CSIDD = "CSIDD"

    VC = "VC"
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


class OrbitState(str, BaseEnum):
    ascending = "ascending"
    descending = "descending"
    either = "either"


class ObservationDirection(str, BaseEnum):
    left = "left"
    right = "right"
    either = "either"


class OrbitalPlane(int, BaseEnum):
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


class CollectionTier(str, BaseEnum):
    urgent = "urgent"
    priority = "priority"
    standard = "standard"
    flexible = "flexible"
    internal = "internal"


class RepeatCollectionTier(str, BaseEnum):
    flexible = "flexible"
    routine = "routine"
    internal = "internal"


class RepeatCycle(int, BaseEnum):
    DAILY = 1
    WEEKLY = 7
    BI_WEEKLY = 14
    MONTHLY = 30


class ArchiveHoldback(str, BaseEnum):
    none = "none"
    one_year = "1_year"
    thirty_day = "30_day"
    permanent = "permanent"


class Polarization(str, BaseEnum):
    HH = "HH"
    VV = "VV"


class LocalTimeOption(str, BaseEnum):
    day = "day"
    night = "night"
    anytime = "anytime"


class OwnershipOption(str, BaseEnum):
    ORG = "ownedByOrganization"
    PUBLIC = "publiclyAvailable"
    SHARED = "sharedWithOrganization"
    PURCHASABLE = "availableForPurchase"

    @classmethod
    def is_valid(cls, option_str: str) -> bool:
        return option_str in list(cls)


class CollectionType(str, BaseEnum):
    SPOTLIGHT = "spotlight"
    SPOTLIGHT_ULTRA = "spotlight_ultra"
    SPOTLIGHT_WIDE = "spotlight_wide"
    STRIPMAP_20 = "stripmap_20"
    STRIPMAP_50 = "stripmap_50"
    STRIPMAP_100 = "stripmap_100"


class SquintMode(str, BaseEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    FORWARD = "forward"
    BACKWARD = "backward"


class AuthHeaderPrefix(Enum):
    BASIC = "Basic"
    TOKEN = "Bearer"
    API_KEY = "ApiKey"
