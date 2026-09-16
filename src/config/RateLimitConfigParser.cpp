#include "config/RateLimitConfigParser.h"
#include <fstream>
#include <stdexcept>
#include <nlohmann/json.hpp>
using json = nlohmann::json;

UserTier RateLimitConfigParser::parseUserTier(const std::string &tierKey)
{
    if (tierKey == "FREE")
    {
        return UserTier::FREE;
    }
    if (tierKey == "PREMIUM")
    {
        return UserTier::PREMIUM;
    }
    throw std::runtime_error("Unknown UserTier: " + tierKey);
}

RateLimitType RateLimitConfigParser::parseRateLimitType(const std::string &typeKey)
{
    if (typeKey == "FIXED_WINDOW")
    {
        return RateLimitType::FIXED_WINDOW;
    }
    if (typeKey == "SLIDING_WINDOW")
    {
        return RateLimitType::SLIDING_WINDOW;
    }
    if (typeKey == "TOKEN_BUCKET")
    {
        return RateLimitType::TOKEN_BUCKET;
    }
    if (typeKey == "LEAKY_BUCKET")
    {
        return RateLimitType::LEAKY_BUCKET;
    }
    throw std::runtime_error("Unknown RateLimitType: " + typeKey);
}

std::map<
    UserTier,
    std::map<RateLimitType, RateLimitConfig>>
RateLimitConfigParser::parseFromFile(
    const std::string &configPath)
{
    std::ifstream file(configPath);
    if (!file.is_open())
    {
        throw std::runtime_error("Unable to open config file");
    }

    json root;
    file >> root;

    std::map<
        UserTier,
        std::map<RateLimitType, RateLimitConfig>>
        configs;

    for (const auto &[tierKey, tierValue] : root.items())
    {
        UserTier tier = parseUserTier(tierKey);

        for (const auto &[typeKey, configJson] : tierValue.items())
        {
            RateLimitType type = parseRateLimitType(typeKey);

            RateLimitConfig config;
            config.maxRequests = configJson.value("maxRequests", 0);
            config.bucketCapacity = configJson.value("bucketCapacity", 0);
            config.refillRatePerSecond = configJson.value("refillRatePerSecond", 0);
            config.windowSizeInSeconds = configJson.value("windowSizeInSeconds", 0);

            configs[tier][type] = config;
        }
    }

    return configs;
}

std::map<UserTier, RateLimitType> RateLimitConfigParser::parsePolicyFromFile(const std::string& policyPath) {
    std::ifstream file(policyPath);
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open policy file: " + policyPath);
    }

    json root;
    file >> root;

    std::map<UserTier, RateLimitType> policy;
    for (const auto& [key, val] : root.items()) {
        policy[parseUserTier(key)] = parseRateLimitType(val.get<std::string>());
    }
    return policy;
}
