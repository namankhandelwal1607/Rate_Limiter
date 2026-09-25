from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, Union

from src.enums import UserTier, RateLimitType


@dataclass
class RateLimitConfig:
    max_requests: int = 0
    bucket_capacity: int = 0
    refill_rate_per_second: int = 0
    window_size_in_seconds: int = 0

    # CamelCase property aliases for C++ parity
    @property
    def maxRequests(self) -> int:
        return self.max_requests

    @property
    def bucketCapacity(self) -> int:
        return self.bucket_capacity

    @property
    def refillRatePerSecond(self) -> int:
        return self.refill_rate_per_second

    @property
    def windowSizeInSeconds(self) -> int:
        return self.window_size_in_seconds


class RateLimitConfigParser:
    @staticmethod
    def _resolve_path(file_path: Union[str, Path]) -> Path:
        p = Path(file_path)
        if p.exists():
            return p
        # Check relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        candidate = project_root / file_path
        if candidate.exists():
            return candidate
        return p

    @staticmethod
    def parse_user_tier(tier_key: str) -> UserTier:
        if tier_key == "FREE":
            return UserTier.FREE
        if tier_key == "PREMIUM":
            return UserTier.PREMIUM
        raise RuntimeError("Unknown UserTier: " + tier_key)

    @staticmethod
    def parse_rate_limit_type(type_key: str) -> RateLimitType:
        if type_key == "FIXED_WINDOW":
            return RateLimitType.FIXED_WINDOW
        if type_key == "SLIDING_WINDOW":
            return RateLimitType.SLIDING_WINDOW
        if type_key == "TOKEN_BUCKET":
            return RateLimitType.TOKEN_BUCKET
        if type_key == "LEAKY_BUCKET":
            return RateLimitType.LEAKY_BUCKET
        raise RuntimeError("Unknown RateLimitType: " + type_key)

    @staticmethod
    def parse_from_file(config_path: Union[str, Path]) -> Dict[UserTier, Dict[RateLimitType, RateLimitConfig]]:
        path = RateLimitConfigParser._resolve_path(config_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                root = json.load(f)
        except Exception:
            raise RuntimeError("Unable to open config file")

        configs: Dict[UserTier, Dict[RateLimitType, RateLimitConfig]] = {}
        for tier_key, tier_value in root.items():
            tier = RateLimitConfigParser.parse_user_tier(tier_key)
            configs[tier] = {}
            for type_key, config_json in tier_value.items():
                limit_type = RateLimitConfigParser.parse_rate_limit_type(type_key)
                config = RateLimitConfig(
                    max_requests=config_json.get("maxRequests", 0),
                    bucket_capacity=config_json.get("bucketCapacity", 0),
                    refill_rate_per_second=config_json.get("refillRatePerSecond", 0),
                    window_size_in_seconds=config_json.get("windowSizeInSeconds", 0),
                )
                configs[tier][limit_type] = config

        return configs

    @staticmethod
    def parse_policy_from_file(policy_path: Union[str, Path]) -> Dict[UserTier, RateLimitType]:
        path = RateLimitConfigParser._resolve_path(policy_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                root = json.load(f)
        except Exception:
            raise RuntimeError("Unable to open policy file: " + str(policy_path))

        policy: Dict[UserTier, RateLimitType] = {}
        for key, val in root.items():
            tier = RateLimitConfigParser.parse_user_tier(key)
            limit_type = RateLimitConfigParser.parse_rate_limit_type(val)
            policy[tier] = limit_type
        return policy

    # CamelCase aliases
    parseUserTier = parse_user_tier
    parseRateLimitType = parse_rate_limit_type
    parseFromFile = parse_from_file
    parsePolicyFromFile = parse_policy_from_file


class RateLimitConfigProvider:
    def __init__(self, config_path: Union[str, Path]):
        self._configs = RateLimitConfigParser.parse_from_file(config_path)

    def get_config(self, tier: UserTier, limit_type: RateLimitType) -> RateLimitConfig:
        tier_configs = self._configs.get(tier)
        if tier_configs is None:
            raise RuntimeError("RateLimitConfigProvider: UserTier not found")
        config = tier_configs.get(limit_type)
        if config is None:
            raise RuntimeError("RateLimitConfigProvider: RateLimitType not found")
        return config

    # CamelCase alias
    getConfig = get_config
