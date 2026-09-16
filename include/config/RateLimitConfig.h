#pragma once

struct RateLimitConfig {
    int maxRequests;            // Max requests allowed in a time window
    int bucketCapacity;         // Max tokens allowed (Token Bucket)
    int refillRatePerSecond;    // Tokens added per second (Token Bucket)
    int windowSizeInSeconds;    // Window size for Fixed/Sliding Window
};
