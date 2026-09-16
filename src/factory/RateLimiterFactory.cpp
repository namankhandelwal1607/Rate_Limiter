#include "factory/RateLimiterFactory.h"

#include <stdexcept>

#include "limiter/FixedWindowRateLimiter.h"
#include "limiter/SlidingWindowRateLimiter.h"
#include "limiter/TokenBucketRateLimiter.h"
#include "limiter/LeakyBucketRateLimiter.h"

RateLimiterFactory::RateLimiterFactory(
    const RateLimitConfigProvider& configProvider
)
    : configProvider_(configProvider) {
}

std::unique_ptr<RateLimiter> RateLimiterFactory::createLimiter(
    UserTier tier,
    RateLimitType type
) const {
    const RateLimitConfig& config =
        configProvider_.getConfig(tier, type);

    switch (type) {
        case RateLimitType::FIXED_WINDOW:
            return std::make_unique<FixedWindowRateLimiter>(config);

        case RateLimitType::SLIDING_WINDOW:
            return std::make_unique<SlidingWindowRateLimiter>(config);

        case RateLimitType::TOKEN_BUCKET:
            return std::make_unique<TokenBucketRateLimiter>(config);

        case RateLimitType::LEAKY_BUCKET:
            return std::make_unique<LeakyBucketRateLimiter>(config);

        default:
            throw std::runtime_error("Unsupported RateLimitType");
    }
}
