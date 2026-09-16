#include "limiter/FixedWindowRateLimiter.h"

#include <chrono>

FixedWindowRateLimiter::FixedWindowRateLimiter(
    const RateLimitConfig &config) : RateLimiter(config),
                                     windowStart_(std::chrono::steady_clock::now())
{
}
bool FixedWindowRateLimiter::allowRequest(const std::string &key)
{
    auto now = std::chrono::steady_clock::now();

    // Calculate how much time has passed since window started
    auto elapsedSeconds =
        std::chrono::duration_cast<std::chrono::seconds>(
            now - windowStart_)
            .count();

    // If window expired, reset counts and window start time
    if (elapsedSeconds >= config_.windowSizeInSeconds)
    {
        requestCounts_.clear();
        windowStart_ = now;
    }

    // Increment request count for this key
    int &count = requestCounts_[key];
    count++;

    // Check if request limit exceeded
    if (count > config_.maxRequests)
    {
        return false;
    }

    return true;
}