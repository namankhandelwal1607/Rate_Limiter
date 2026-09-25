from pathlib import Path
from typing import Dict, Tuple, Union

from src.config import RateLimitConfigParser, RateLimitConfigProvider
from src.enums import RateLimitType, UserTier
from src.factory import RateLimiterFactory
from src.limiter import RateLimiter


class RateLimiterService:
    def __init__(self, factory: RateLimiterFactory):
        self._factory = factory
        self._limiters: Dict[Tuple[UserTier, RateLimitType], RateLimiter] = {}

    def allow_request(self, tier: UserTier, limit_type: RateLimitType, key: str) -> bool:
        limiter_key = (tier, limit_type)
        if limiter_key not in self._limiters:
            self._limiters[limiter_key] = self._factory.create_limiter(tier, limit_type)
        return self._limiters[limiter_key].allow_request(key)

    # CamelCase alias
    allowRequest = allow_request


class RateLimiterManager:
    def __init__(
        self,
        config_path: Union[str, Path] = "config/rate_limit_config.json",
        policy_path: Union[str, Path] = "config/rate_limit_policy.json",
    ):
        self._config_provider = RateLimitConfigProvider(config_path)
        self._factory = RateLimiterFactory(self._config_provider)
        self._service = RateLimiterService(self._factory)
        self._policy = RateLimitConfigParser.parse_policy_from_file(policy_path)

    def allow_request(self, user_id: str, user_tier_str: Union[str, UserTier]) -> bool:
        if isinstance(user_tier_str, UserTier):
            tier = user_tier_str
        else:
            tier = RateLimitConfigParser.parse_user_tier(user_tier_str)

        limit_type = self._policy.get(tier)
        if limit_type is None:
            raise RuntimeError("No rate limit policy defined for this user tier")

        return self._service.allow_request(tier, limit_type, user_id)

    # CamelCase alias
    allowRequest = allow_request
