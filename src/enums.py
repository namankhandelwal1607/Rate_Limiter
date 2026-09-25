from enum import Enum


class UserTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"


class RateLimitType(str, Enum):
    FIXED_WINDOW = "FIXED_WINDOW"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    TOKEN_BUCKET = "TOKEN_BUCKET"
    LEAKY_BUCKET = "LEAKY_BUCKET"
