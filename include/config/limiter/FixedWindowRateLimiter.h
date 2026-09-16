#pragma once
#include <string>
#include <unordered_map>
#include <chrono>
#include "limiter/RateLimiter.h"

class FixedWindowRateLimiter : public RateLimiter {
public:
    explicit FixedWindowRateLimiter(const RateLimitConfig& config);

    bool allowRequest(const std::string& key) override;

private:
    // Stores request count per key for the current window
    std::unordered_map<std::string, int> requestCounts_;

    // Start time of the current window
    std::chrono::steady_clock::time_point windowStart_;
};
