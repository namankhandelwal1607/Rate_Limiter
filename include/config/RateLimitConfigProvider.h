#pragma once

#include <map>
#include <string>

#include "enums/UserTier.h"
#include "enums/RateLimitType.h"
#include "config/RateLimitConfig.h"


class RateLimitConfigProvider {
public:
    explicit RateLimitConfigProvider(const std::string& configPath);

    const RateLimitConfig& getConfig(
        UserTier tier,
        RateLimitType type
    ) const;

private:
    std::map<
        UserTier,
        std::map<RateLimitType, RateLimitConfig>
    > configs_;
};
