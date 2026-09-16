#pragma once

#include <string>
#include <unordered_map>
#include <deque>
#include <chrono>

#include "limiter/RateLimiter.h"

class SlidingWindowRateLimiter : public RateLimiter {
public:
    explicit SlidingWindowRateLimiter(const RateLimitConfig& config);

    bool allowRequest(const std::string& key) override;

private:
    // Stores timestamps of requests per key
    std::unordered_map<
        std::string,
        std::deque<std::chrono::steady_clock::time_point>
    > requestTimestamps_;
};
