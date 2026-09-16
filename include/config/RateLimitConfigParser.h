#pragma once

#include <string>
#include <map>

#include "enums/UserTier.h"
#include "enums/RateLimitType.h"
#include "RateLimitConfig.h"


class RateLimitConfigParser {
public:
    static std::map<UserTier,std::map<RateLimitType, RateLimitConfig> > parseFromFile(const std::string& configPath);
    static std::map<UserTier, RateLimitType> parsePolicyFromFile(const std::string& policyPath);

    static UserTier parseUserTier(const std::string& tierKey);
    static RateLimitType parseRateLimitType(const std::string& typeKey);
};
