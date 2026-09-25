import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure src is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.enums import UserTier, RateLimitType
from src.config import RateLimitConfig, RateLimitConfigParser, RateLimitConfigProvider
from src.limiter import (
    RateLimiter,
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    LeakyBucketRateLimiter,
)
from src.factory import RateLimiterFactory
from src.service import RateLimiterService, RateLimiterManager
from src.main import main


class TestRateLimiterEnums(unittest.TestCase):
    def test_user_tier(self):
        self.assertEqual(UserTier.FREE.value, "FREE")
        self.assertEqual(UserTier.PREMIUM.value, "PREMIUM")

    def test_rate_limit_type(self):
        self.assertEqual(RateLimitType.FIXED_WINDOW.value, "FIXED_WINDOW")
        self.assertEqual(RateLimitType.SLIDING_WINDOW.value, "SLIDING_WINDOW")
        self.assertEqual(RateLimitType.TOKEN_BUCKET.value, "TOKEN_BUCKET")
        self.assertEqual(RateLimitType.LEAKY_BUCKET.value, "LEAKY_BUCKET")


class TestConfig(unittest.TestCase):
    def test_config_dataclass_properties(self):
        cfg = RateLimitConfig(
            max_requests=10,
            bucket_capacity=15,
            refill_rate_per_second=2,
            window_size_in_seconds=30,
        )
        self.assertEqual(cfg.maxRequests, 10)
        self.assertEqual(cfg.bucketCapacity, 15)
        self.assertEqual(cfg.refillRatePerSecond, 2)
        self.assertEqual(cfg.windowSizeInSeconds, 30)

    def test_parser_helpers(self):
        self.assertEqual(RateLimitConfigParser.parse_user_tier("FREE"), UserTier.FREE)
        self.assertEqual(RateLimitConfigParser.parse_user_tier("PREMIUM"), UserTier.PREMIUM)
        with self.assertRaises(RuntimeError) as ctx:
            RateLimitConfigParser.parse_user_tier("UNKNOWN")
        self.assertIn("Unknown UserTier: UNKNOWN", str(ctx.exception))

        self.assertEqual(
            RateLimitConfigParser.parse_rate_limit_type("FIXED_WINDOW"),
            RateLimitType.FIXED_WINDOW,
        )
        self.assertEqual(
            RateLimitConfigParser.parse_rate_limit_type("SLIDING_WINDOW"),
            RateLimitType.SLIDING_WINDOW,
        )
        self.assertEqual(
            RateLimitConfigParser.parse_rate_limit_type("TOKEN_BUCKET"),
            RateLimitType.TOKEN_BUCKET,
        )
        self.assertEqual(
            RateLimitConfigParser.parse_rate_limit_type("LEAKY_BUCKET"),
            RateLimitType.LEAKY_BUCKET,
        )
        with self.assertRaises(RuntimeError) as ctx:
            RateLimitConfigParser.parse_rate_limit_type("INVALID")
        self.assertIn("Unknown RateLimitType: INVALID", str(ctx.exception))

    def test_parse_from_file(self):
        configs = RateLimitConfigParser.parse_from_file("config/rate_limit_config.json")
        self.assertIn(UserTier.FREE, configs)
        self.assertIn(UserTier.PREMIUM, configs)
        self.assertEqual(configs[UserTier.FREE][RateLimitType.FIXED_WINDOW].max_requests, 5)
        self.assertEqual(configs[UserTier.FREE][RateLimitType.FIXED_WINDOW].window_size_in_seconds, 60)
        self.assertEqual(configs[UserTier.PREMIUM][RateLimitType.TOKEN_BUCKET].bucket_capacity, 20)
        self.assertEqual(configs[UserTier.PREMIUM][RateLimitType.TOKEN_BUCKET].refill_rate_per_second, 5)

    def test_parse_policy_from_file(self):
        policy = RateLimitConfigParser.parse_policy_from_file("config/rate_limit_policy.json")
        self.assertEqual(policy[UserTier.FREE], RateLimitType.FIXED_WINDOW)
        self.assertEqual(policy[UserTier.PREMIUM], RateLimitType.SLIDING_WINDOW)

    def test_parse_missing_files(self):
        with self.assertRaises(RuntimeError) as ctx:
            RateLimitConfigParser.parse_from_file("non_existent_config.json")
        self.assertIn("Unable to open config file", str(ctx.exception))

        with self.assertRaises(RuntimeError) as ctx:
            RateLimitConfigParser.parse_policy_from_file("non_existent_policy.json")
        self.assertIn("Unable to open policy file", str(ctx.exception))

    def test_config_provider(self):
        provider = RateLimitConfigProvider("config/rate_limit_config.json")
        cfg = provider.get_config(UserTier.FREE, RateLimitType.FIXED_WINDOW)
        self.assertEqual(cfg.max_requests, 5)
        # Test camelCase alias
        cfg_alias = provider.getConfig(UserTier.FREE, RateLimitType.FIXED_WINDOW)
        self.assertEqual(cfg_alias.maxRequests, 5)


class TestAlgorithms(unittest.TestCase):
    def test_fixed_window_rate_limiter(self):
        config = RateLimitConfig(max_requests=3, window_size_in_seconds=60)
        limiter = FixedWindowRateLimiter(config)

        # Allow 3 requests
        self.assertTrue(limiter.allow_request("user1"))
        self.assertTrue(limiter.allow_request("user1"))
        self.assertTrue(limiter.allow_request("user1"))
        # 4th request blocked
        self.assertFalse(limiter.allow_request("user1"))

        # user2 should still be allowed
        self.assertTrue(limiter.allow_request("user2"))

        # Simulate window expiration
        current_time = time.monotonic()
        with patch("time.monotonic", return_value=current_time + 61):
            self.assertTrue(limiter.allow_request("user1"))

    def test_sliding_window_rate_limiter(self):
        config = RateLimitConfig(max_requests=2, window_size_in_seconds=10)
        limiter = SlidingWindowRateLimiter(config)

        t0 = 100.0
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user1"))
            self.assertTrue(limiter.allow_request("user1"))
            self.assertFalse(limiter.allow_request("user1"))

        # User2 unaffected
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user2"))

        # Advance 11 seconds - old timestamps should expire
        with patch("time.monotonic", return_value=t0 + 11.0):
            self.assertTrue(limiter.allow_request("user1"))
            self.assertTrue(limiter.allow_request("user1"))
            self.assertFalse(limiter.allow_request("user1"))

    def test_token_bucket_rate_limiter(self):
        config = RateLimitConfig(bucket_capacity=3, refill_rate_per_second=1)
        limiter = TokenBucketRateLimiter(config)

        t0 = 1000.0
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user1"))  # 3 -> 2
            self.assertTrue(limiter.allow_request("user1"))  # 2 -> 1
            self.assertTrue(limiter.allow_request("user1"))  # 1 -> 0
            self.assertFalse(limiter.allow_request("user1")) # 0 -> rejected

        # User 2 has separate bucket
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user2"))

        # Advance 2 seconds -> refills 2 tokens
        with patch("time.monotonic", return_value=t0 + 2.0):
            self.assertTrue(limiter.allow_request("user1"))  # 2 -> 1
            self.assertTrue(limiter.allow_request("user1"))  # 1 -> 0
            self.assertFalse(limiter.allow_request("user1")) # 0 -> rejected

    def test_leaky_bucket_rate_limiter(self):
        config = RateLimitConfig(bucket_capacity=3, refill_rate_per_second=1)
        limiter = LeakyBucketRateLimiter(config)

        t0 = 2000.0
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user1"))  # 0 -> 1
            self.assertTrue(limiter.allow_request("user1"))  # 1 -> 2
            self.assertTrue(limiter.allow_request("user1"))  # 2 -> 3
            self.assertFalse(limiter.allow_request("user1")) # 3 >= capacity, rejected

        # User 2 separate
        with patch("time.monotonic", return_value=t0):
            self.assertTrue(limiter.allow_request("user2"))

        # Advance 2 seconds -> leaks 2 requests
        with patch("time.monotonic", return_value=t0 + 2.0):
            self.assertTrue(limiter.allow_request("user1"))  # 1 -> 2
            self.assertTrue(limiter.allow_request("user1"))  # 2 -> 3
            self.assertFalse(limiter.allow_request("user1")) # 3 >= capacity, rejected


class TestManagerAndService(unittest.TestCase):
    def test_manager_integration(self):
        manager = RateLimiterManager()

        # FREE tier uses FIXED_WINDOW (max 5 requests)
        for i in range(5):
            self.assertTrue(manager.allow_request("free_user", "FREE"))
        self.assertFalse(manager.allow_request("free_user", "FREE"))

        # PREMIUM tier uses SLIDING_WINDOW (max 20 requests)
        for i in range(20):
            self.assertTrue(manager.allow_request("prem_user", "PREMIUM"))
        self.assertFalse(manager.allow_request("prem_user", "PREMIUM"))

        # allowRequest camelCase alias
        self.assertFalse(manager.allowRequest("free_user", "FREE"))

        # UserTier enum can also be passed
        self.assertFalse(manager.allow_request("free_user", UserTier.FREE))

    def test_manager_unknown_tier(self):
        manager = RateLimiterManager()
        with self.assertRaises(RuntimeError):
            manager.allow_request("user", "NON_EXISTENT")

    def test_manager_missing_policy_tier(self):
        # Create a temp policy file without PREMIUM
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            f.write(json.dumps({"FREE": "FIXED_WINDOW"}))
            f.flush()
            temp_policy = f.name

        try:
            manager = RateLimiterManager(policy_path=temp_policy)
            self.assertTrue(manager.allow_request("user", "FREE"))
            with self.assertRaises(RuntimeError) as ctx:
                manager.allow_request("user", "PREMIUM")
            self.assertIn("No rate limit policy defined for this user tier", str(ctx.exception))
        finally:
            Path(temp_policy).unlink(missing_ok=True)


class TestCLI(unittest.TestCase):
    def test_main_flow(self):
        # Provide inputs: user1 FREE (5 times, 6th rejected), invalid tier, exit
        input_data = (
            "alice\nFREE\n"
            "alice\nFREE\n"
            "alice\nFREE\n"
            "alice\nFREE\n"
            "alice\nFREE\n"
            "alice\nFREE\n"
            "bob\nINVALID\n"
            "exit\n"
        )
        stdin_backup = sys.stdin
        stdout_backup = sys.stdout
        try:
            sys.stdin = io.StringIO(input_data)
            out = io.StringIO()
            sys.stdout = out
            code = main()
            self.assertEqual(code, 0)
            output = out.getvalue()
            self.assertIn("Rate Limiter Service Started.", output)
            self.assertIn(" Request ALLOWED", output)
            self.assertIn("Request BLOCKED (rate limit exceeded)", output)
            self.assertIn("Error: Unknown UserTier: INVALID", output)
            self.assertIn("Shutting down...", output)
        finally:
            sys.stdin = stdin_backup
            sys.stdout = stdout_backup


class TestFactory(unittest.TestCase):
    def test_factory_creation(self):
        provider = RateLimitConfigProvider("config/rate_limit_config.json")
        factory = RateLimiterFactory(provider)

        fw = factory.create_limiter(UserTier.FREE, RateLimitType.FIXED_WINDOW)
        self.assertIsInstance(fw, FixedWindowRateLimiter)

        sw = factory.create_limiter(UserTier.PREMIUM, RateLimitType.SLIDING_WINDOW)
        self.assertIsInstance(sw, SlidingWindowRateLimiter)

        tb = factory.create_limiter(UserTier.FREE, RateLimitType.TOKEN_BUCKET)
        self.assertIsInstance(tb, TokenBucketRateLimiter)

        lb = factory.create_limiter(UserTier.FREE, RateLimitType.LEAKY_BUCKET)
        self.assertIsInstance(lb, LeakyBucketRateLimiter)

        # Test camelCase alias
        fw_alias = factory.createLimiter(UserTier.FREE, RateLimitType.FIXED_WINDOW)
        self.assertIsInstance(fw_alias, FixedWindowRateLimiter)

    def test_factory_unsupported_type(self):
        class DummyProvider:
            def get_config(self, tier, limit_type):
                return RateLimitConfig()

        factory = RateLimiterFactory(DummyProvider())
        with self.assertRaises(RuntimeError) as ctx:
            factory.create_limiter(UserTier.FREE, "INVALID_TYPE")
        self.assertIn("Unsupported RateLimitType", str(ctx.exception))


class TestConfigEdgeCases(unittest.TestCase):
    def test_provider_missing_type(self):
        # Create a config json missing TOKEN_BUCKET
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            data = {"FREE": {"FIXED_WINDOW": {"maxRequests": 10}}}
            f.write(json.dumps(data))
            f.flush()
            temp_config = f.name

        try:
            provider = RateLimitConfigProvider(temp_config)
            with self.assertRaises(RuntimeError) as ctx:
                provider.get_config(UserTier.FREE, RateLimitType.TOKEN_BUCKET)
            self.assertIn("RateLimitConfigProvider: RateLimitType not found", str(ctx.exception))

            with self.assertRaises(RuntimeError) as ctx:
                provider.get_config(UserTier.PREMIUM, RateLimitType.FIXED_WINDOW)
            self.assertIn("RateLimitConfigProvider: UserTier not found", str(ctx.exception))
        finally:
            Path(temp_config).unlink(missing_ok=True)

    def test_config_defaults_to_zero(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            data = {"FREE": {"FIXED_WINDOW": {}}}
            f.write(json.dumps(data))
            f.flush()
            temp_config = f.name

        try:
            provider = RateLimitConfigProvider(temp_config)
            cfg = provider.get_config(UserTier.FREE, RateLimitType.FIXED_WINDOW)
            self.assertEqual(cfg.max_requests, 0)
            self.assertEqual(cfg.bucket_capacity, 0)
            self.assertEqual(cfg.refill_rate_per_second, 0)
            self.assertEqual(cfg.window_size_in_seconds, 0)
        finally:
            Path(temp_config).unlink(missing_ok=True)


class TestAlgorithmsAdvanced(unittest.TestCase):
    def test_token_bucket_clamping_and_drain(self):
        config = RateLimitConfig(bucket_capacity=5, refill_rate_per_second=2)
        limiter = TokenBucketRateLimiter(config)

        t = 5000.0
        # Drain all 5 tokens
        with patch("time.monotonic", return_value=t):
            for _ in range(5):
                self.assertTrue(limiter.allow_request("user_tb"))
            self.assertFalse(limiter.allow_request("user_tb"))

        # Wait 100 seconds: tokens should be clamped to 5 (not 200!)
        t += 100.0
        with patch("time.monotonic", return_value=t):
            for _ in range(5):
                self.assertTrue(limiter.allow_request("user_tb"))
            self.assertFalse(limiter.allow_request("user_tb"))

    def test_leaky_bucket_clamping_to_zero(self):
        config = RateLimitConfig(bucket_capacity=3, refill_rate_per_second=5)
        limiter = LeakyBucketRateLimiter(config)

        t = 6000.0
        with patch("time.monotonic", return_value=t):
            self.assertTrue(limiter.allow_request("user_lb"))  # queued = 1

        # Wait 100 seconds: queued requests leak down to max(0, 1 - 500) = 0
        t += 100.0
        with patch("time.monotonic", return_value=t):
            self.assertTrue(limiter.allow_request("user_lb"))  # queued: 0 -> 1
            self.assertTrue(limiter.allow_request("user_lb"))  # queued: 1 -> 2
            self.assertTrue(limiter.allow_request("user_lb"))  # queued: 2 -> 3
            self.assertFalse(limiter.allow_request("user_lb")) # 3 >= capacity -> rejected

    def test_fixed_window_resets_all_keys(self):
        config = RateLimitConfig(max_requests=1, window_size_in_seconds=10)
        limiter = FixedWindowRateLimiter(config)

        t = 7000.0
        with patch("time.monotonic", return_value=t):
            self.assertTrue(limiter.allow_request("u1"))
            self.assertFalse(limiter.allow_request("u1"))
            self.assertTrue(limiter.allow_request("u2"))
            self.assertFalse(limiter.allow_request("u2"))

        # Advance 11 seconds: window resets for all users
        with patch("time.monotonic", return_value=t + 11.0):
            self.assertTrue(limiter.allow_request("u1"))
            self.assertTrue(limiter.allow_request("u2"))


if __name__ == "__main__":
    unittest.main()

