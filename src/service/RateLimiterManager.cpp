#include "service/RateLimiterManager.h"
#include "config/RateLimitConfigParser.h"
#include <fstream>
#include <stdexcept>
#include <iostream>

RateLimiterManager::RateLimiterManager() 
    : RateLimiterManager("config/rate_limit_config.json", "config/rate_limit_policy.json") 
{
}

RateLimiterManager::RateLimiterManager(const std::string& configPath, const std::string& policyPath)
    : configProvider_(configPath),
      factory_(configProvider_),
      service_(factory_) 
{
    policy_ = RateLimitConfigParser::parsePolicyFromFile(policyPath);
}

bool RateLimiterManager::allowRequest(const std::string& userId, const std::string& userTierStr) {
    // Convert string to enum using the exposed helper
    UserTier tier = RateLimitConfigParser::parseUserTier(userTierStr);

    // Look up the strategy in our loaded policy
    auto it = policy_.find(tier);
    if (it == policy_.end()) {
        throw std::runtime_error("No rate limit policy defined for this user tier");
    }

    RateLimitType type = it->second;

    // Delegate to the service
    return service_.allowRequest(tier, type, userId);
}
