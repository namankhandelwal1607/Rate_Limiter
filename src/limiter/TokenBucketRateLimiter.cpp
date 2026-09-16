#include "limiter/TokenBucketRateLimiter.h"

TokenBucketRateLimiter::TokenBucketRateLimiter(
    const RateLimitConfig& config
) : RateLimiter(config) {
}

bool TokenBucketRateLimiter::allowRequest(const std::string& key) {
    auto now = std::chrono::steady_clock::now();
    auto& bucket = buckets_[key];

    // First-time initialization
    if (bucket.lastRefill.time_since_epoch().count() == 0) {
        bucket.tokens = config_.bucketCapacity;
        bucket.lastRefill = now;
    }

    // Refill tokens
    auto elapsedSeconds =
        std::chrono::duration_cast<std::chrono::seconds>(
            now - bucket.lastRefill
        ).count();

    bucket.tokens = std::min(
        static_cast<double>(config_.bucketCapacity),
        bucket.tokens + elapsedSeconds * config_.refillRatePerSecond
    );

    bucket.lastRefill = now;

    if (bucket.tokens < 1.0) {
        return false;
    }

    bucket.tokens -= 1.0;
    return true;
}
