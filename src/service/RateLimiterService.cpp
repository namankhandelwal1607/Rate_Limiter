#include "service/RateLimiterService.h"

RateLimiterService::RateLimiterService(
    RateLimiterFactory &factory)
    : factory_(factory)
{
}

bool RateLimiterService::allowRequest(
    UserTier tier,
    RateLimitType type,
    const std::string &key)
{
    auto limiterKey = std::make_pair(tier, type);

    // Create limiter lazily (only once)
    auto it = limiters_.find(limiterKey);
    if (it == limiters_.end())
    {
        limiters_[limiterKey] =
            factory_.createLimiter(tier, type);
    }

    return limiters_[limiterKey]->allowRequest(key);
}
