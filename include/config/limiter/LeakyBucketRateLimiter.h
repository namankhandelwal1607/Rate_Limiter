#pragma once

#include <string>
#include <unordered_map>
#include <chrono>

#include "limiter/RateLimiter.h"

class LeakyBucketRateLimiter : public RateLimiter {
public:
    explicit LeakyBucketRateLimiter(const RateLimitConfig& config);

    bool allowRequest(const std::string& key) override;

private:
    struct Bucket {
        int queuedRequests;
        std::chrono::steady_clock::time_point lastLeak;
    };

    std::unordered_map<std::string, Bucket> buckets_;
};
