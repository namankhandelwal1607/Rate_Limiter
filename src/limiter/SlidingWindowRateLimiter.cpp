#include "limiter/SlidingWindowRateLimiter.h"

SlidingWindowRateLimiter::SlidingWindowRateLimiter(
    const RateLimitConfig& config
) : RateLimiter(config) {
}

bool SlidingWindowRateLimiter::allowRequest(const std::string& key) {
    auto now = std::chrono::steady_clock::now();
    auto& timestamps = requestTimestamps_[key];

    // Remove requests outside the window
    while (!timestamps.empty()) {
        auto elapsed =
            std::chrono::duration_cast<std::chrono::seconds>(
                now - timestamps.front()
            ).count();

        if (elapsed >= config_.windowSizeInSeconds) {
            timestamps.pop_front();
        } else {
            break;
        }
    }

    if (timestamps.size() >= static_cast<size_t>(config_.maxRequests)) {
        return false;
    }

    timestamps.push_back(now);
    return true;
}
