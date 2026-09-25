<img width="7808" height="4018" alt="image" src="https://github.com/user-attachments/assets/4b14cb83-9017-4bf5-aa25-b0d4adab3caa" />

# Rate Limiter Service

A high-performance, microservice-ready Rate Limiter library in Python. It features a manager-based architecture that simplifies integration, utilizing configurable policies and distinct pluggable rate limiting strategies (Fixed Window, Sliding Window, Token Bucket, Leaky Bucket).

## 🏗️ Architecture

The system is designed for easy integration into existing Python microservices and web frameworks:

-   **`RateLimiterManager`**: The single entry point. Handles initialization, config loading, and policy management.
-   **Configuration**:
    -   `config/rate_limit_config.json`: Defines the rules (e.g., max requests, window size, refill rate) for each strategy.
    -   `config/rate_limit_policy.json`: Maps user tiers to strategies (e.g., "FREE" -> "FIXED_WINDOW", "PREMIUM" -> "SLIDING_WINDOW").
-   **Strategies**: Pluggable implementations for different rate limiting algorithms (Fixed Window, Sliding Window, Token Bucket, Leaky Bucket).
-   **Standard Library Only**: Zero external dependencies (uses built-in `json`, `time`, `collections`, `dataclasses`, `enum`, `abc`).

## 🚀 Quick Start

### 1. Run Interactive Demo
The demo app acts as a mock server, accepting `userId` and `Tier` to check limits interactively:

```bash
python src/main.py
```

### 2. Run Test Suite
Comprehensive unit and integration tests covering all algorithms, edge cases, and configuration parsing:

```bash
python -m unittest discover -s tests -v
```

## 💻 Microservice Integration

To use this in your production service, instantiate the manager once at startup and execute a one-line check per request:

### Code Example

```python
from src.service import RateLimiterManager

# Initialize once at startup (loads config/rate_limit_config.json & config/rate_limit_policy.json)
rate_limiter = RateLimiterManager()

def handle_request(user_id: str, tier: str) -> bool:
    # One-line check
    if rate_limiter.allow_request(user_id, tier):
        # ... Process Request ...
        return True
    else:
        # ... Return 429 Too Many Requests ...
        return False
```

## ⚙️ Configuration

### 1. Define Tier Policies (`config/rate_limit_policy.json`)
```json
{
  "FREE": "FIXED_WINDOW",
  "PREMIUM": "SLIDING_WINDOW"
}
```

### 2. Configure Algorithm Parameters (`config/rate_limit_config.json`)
```json
{
  "FREE": {
    "FIXED_WINDOW": {
      "maxRequests": 5,
      "windowSizeInSeconds": 60
    },
    "TOKEN_BUCKET": {
      "bucketCapacity": 5,
      "refillRatePerSecond": 1
    }
  },
  "PREMIUM": {
    "SLIDING_WINDOW": {
      "maxRequests": 20,
      "windowSizeInSeconds": 60
    },
    "TOKEN_BUCKET": {
      "bucketCapacity": 20,
      "refillRatePerSecond": 5
    }
  }
}
```

## 📂 Project Structure

-   `src/service/`: Manager and service orchestration ([`RateLimiterManager`](src/service/__init__.py), [`RateLimiterService`](src/service/__init__.py)).
-   `src/config/`: Configuration parsing and provider ([`RateLimitConfigParser`](src/config/__init__.py), [`RateLimitConfigProvider`](src/config/__init__.py)).
-   `src/limiter/`: Algorithm implementations ([`FixedWindowRateLimiter`](src/limiter/__init__.py), [`SlidingWindowRateLimiter`](src/limiter/__init__.py), [`TokenBucketRateLimiter`](src/limiter/__init__.py), [`LeakyBucketRateLimiter`](src/limiter/__init__.py)).
-   `src/factory/`: Factory pattern implementation ([`RateLimiterFactory`](src/factory/__init__.py)).
-   `src/enums.py`: Strongly-typed enum definitions ([`UserTier`](src/enums.py), [`RateLimitType`](src/enums.py)).
-   `src/main.py`: Interactive CLI demo application.
-   `tests/`: Unit and integration test suite.
