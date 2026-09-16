#pragma once

#include <string>
#include <unordered_map>
#include <chrono>

#include "limiter/RateLimiter.h"

class TokenBucketRateLimiter : public RateLimiter {
public:
    explicit TokenBucketRateLimiter(const RateLimitConfig& config);

    bool allowRequest(const std::string& key) override;

private:
    struct Bucket {
        double tokens;
        std::chrono::steady_clock::time_point lastRefill;
    };

    std::unordered_map<std::string, Bucket> buckets_;
};
