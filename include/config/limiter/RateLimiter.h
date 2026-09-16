#pragma once

#include <string>
#include "config/RateLimitConfig.h"


class RateLimiter {
public:
    explicit RateLimiter(const RateLimitConfig& config) : config_(config) {}
    virtual ~RateLimiter() = default;
    // Returns true if request is allowed, false otherwise
    virtual bool allowRequest(const std::string& key) = 0;

protected:
    const RateLimitConfig& config_;
};
