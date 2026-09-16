#pragma once

#include <memory>

#include "enums/RateLimitType.h"
#include "config/RateLimitConfigProvider.h"
#include "limiter/RateLimiter.h"
#include "limiter/FixedWindowRateLimiter.h"

/*
 * RateLimiterFactory
 *
 * Responsible for creating appropriate RateLimiter instances
 * based on RateLimitType.
 */
class RateLimiterFactory {
public:
    explicit RateLimiterFactory(
        const RateLimitConfigProvider& configProvider
    );

    std::unique_ptr<RateLimiter> createLimiter(
        UserTier tier,
        RateLimitType type
    ) const;

private:
    const RateLimitConfigProvider& configProvider_;
};
