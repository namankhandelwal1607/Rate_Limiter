#pragma once
#include <memory>
#include <string>
#include "factory/RateLimiterFactory.h"
#include "limiter/RateLimiter.h"
#include "enums/UserTier.h"
#include "enums/RateLimitType.h"

/*
 * RateLimiterService
 *
 * High-level service used by application code.
 * Owns rate limiter instances and exposes a simple API.
 */
class RateLimiterService {
public:
    explicit RateLimiterService(
        RateLimiterFactory& factory
    );

    // Check whether a request is allowed
    bool allowRequest(
        UserTier tier,
        RateLimitType type,
        const std::string& key
    );

private:
    RateLimiterFactory& factory_;

    // For now, one limiter per (tier + type)
    // In real systems this can be per route / API
    std::map<
        std::pair<UserTier, RateLimitType>,
        std::unique_ptr<RateLimiter>
    > limiters_;
};
