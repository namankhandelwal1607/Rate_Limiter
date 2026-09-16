#include "config/RateLimitConfigProvider.h"
#include "config/RateLimitConfigParser.h"
#include <stdexcept>

RateLimitConfigProvider::RateLimitConfigProvider(
    const std::string& configPath
) {
    configs_ = RateLimitConfigParser::parseFromFile(configPath);
}


const RateLimitConfig& RateLimitConfigProvider::getConfig(
    UserTier tier,
    RateLimitType type
) const {
    auto tierIt = configs_.find(tier);
    if (tierIt == configs_.end()) {
        throw std::runtime_error("RateLimitConfigProvider: UserTier not found");
    }

    auto typeIt = tierIt->second.find(type);
    if (typeIt == tierIt->second.end()) {
        throw std::runtime_error("RateLimitConfigProvider: RateLimitType not found");
    }

    return typeIt->second;
}

