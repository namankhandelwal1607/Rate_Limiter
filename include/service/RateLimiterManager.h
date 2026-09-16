#pragma once

#include <string>
#include <map>
#include "config/RateLimitConfigProvider.h"
#include "factory/RateLimiterFactory.h"
#include "service/RateLimiterService.h"
#include "enums/UserTier.h"
#include "enums/RateLimitType.h"

// High-level manager to simplify usage for microservices
class RateLimiterManager {
public:
    // Uses default paths: "config/rate_limit_config.json" and "config/rate_limit_policy.json"
    RateLimiterManager();

    // Allows specifying custom paths
    RateLimiterManager(const std::string& configPath, const std::string& policyPath);

    // Main entry point: Check if a request is allowed
    // Returns true if allowed, false if blocked
    // Throws std::exception if inputs are invalid
    bool allowRequest(const std::string& userId, const std::string& userTierStr);

private:
    // Components
    RateLimitConfigProvider configProvider_;
    RateLimiterFactory factory_;
    RateLimiterService service_;

    // Internal mapping of Tier -> Strategy (from policy file)
    std::map<UserTier, RateLimitType> policy_;
};
