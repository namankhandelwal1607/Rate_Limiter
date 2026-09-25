from src.config import RateLimitConfigProvider
from src.enums import RateLimitType, UserTier
from src.limiter import (
    FixedWindowRateLimiter,
    LeakyBucketRateLimiter,
    RateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
)


class RateLimiterFactory:
    def __init__(self, config_provider: RateLimitConfigProvider):
        self._config_provider = config_provider

    def create_limiter(self, tier: UserTier, limit_type: RateLimitType) -> RateLimiter:
        config = self._config_provider.get_config(tier, limit_type)

        if limit_type == RateLimitType.FIXED_WINDOW:
            return FixedWindowRateLimiter(config)
        elif limit_type == RateLimitType.SLIDING_WINDOW:
            return SlidingWindowRateLimiter(config)
        elif limit_type == RateLimitType.TOKEN_BUCKET:
            return TokenBucketRateLimiter(config)
        elif limit_type == RateLimitType.LEAKY_BUCKET:
            return LeakyBucketRateLimiter(config)
        else:
            raise RuntimeError("Unsupported RateLimitType")

    # CamelCase alias
    createLimiter = create_limiter
