#include "limiter/LeakyBucketRateLimiter.h"

LeakyBucketRateLimiter::LeakyBucketRateLimiter(
    const RateLimitConfig& config
) : RateLimiter(config) {
}

bool LeakyBucketRateLimiter::allowRequest(const std::string& key) {
    auto now = std::chrono::steady_clock::now();
    auto& bucket = buckets_[key];

    // First-time initialization
    if (bucket.lastLeak.time_since_epoch().count() == 0) {
        bucket.queuedRequests = 0;
        bucket.lastLeak = now;
    }

    // Leak requests
    auto elapsedSeconds =
        std::chrono::duration_cast<std::chrono::seconds>(
            now - bucket.lastLeak
        ).count();

    int leaked = elapsedSeconds * config_.refillRatePerSecond;
    bucket.queuedRequests =
        std::max(0, bucket.queuedRequests - leaked);

    bucket.lastLeak = now;

    if (bucket.queuedRequests >= config_.bucketCapacity) {
        return false;
    }

    bucket.queuedRequests++;
    return true;
}
