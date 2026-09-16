<img width="7808" height="4018" alt="image" src="https://github.com/user-attachments/assets/4b14cb83-9017-4bf5-aa25-b0d4adab3caa" />

# Rate Limiter Service

A high-performance, microservice-ready Rate Limiter library in C++. It features a manager-based architecture that simplifies integration, utilizing configurable policies and distinct rate limiting strategies (Fixed Window, Sliding Window, Token Bucket, Leaky Bucket).

## 🏗️ Architecture

The system is designed for easy integration into existing C++ microservices:

-   **`RateLimiterManager`**: The single entry point. Handles initialization, config loading, and policy management.
-   **Configuration**:
    -   `config/rate_limit_config.json`: Defines the rules (e.g., 5 req/sec) for each strategy.
    -   `config/rate_limit_policy.json`: Maps user tiers to strategies (e.g., "FREE" -> "FIXED_WINDOW").
-   **Strategies**: Pluggable implementations for different rate limiting algorithms.

## 🚀 Quick Start

### 1. Build
The project requires a C++17 compiler and `nlohmann/json`.

```bash
# 1. Download JSON library (if not present)
mkdir -p include/nlohmann
curl -L https://github.com/nlohmann/json/releases/download/v3.11.2/json.hpp -o include/nlohmann/json.hpp

# 2. Compile
g++ -std=c++17 -Iinclude src/main.cpp src/service/RateLimiterManager.cpp src/config/*.cpp src/factory/*.cpp src/limiter/*.cpp src/service/RateLimiterService.cpp -o rate_limiter
```

### 2. Configure
Define your tiers in `config/rate_limit_policy.json`:
```json
{
  "FREE": "FIXED_WINDOW",
  "PREMIUM": "SLIDING_WINDOW"
}
```

### 3. Run Demo
```bash
./rate_limiter
```
*The demo app acts as a mock server, accepting `userId` and `Tier` to check limits interactively.*

## 💻 Microservice Integration

To use this in your production service, simply include the manager and instantiate it efficiently (e.g., as a singleton or scoped service).

### Code Example

```cpp
#include "service/RateLimiterManager.h"

// Initialize once at startup (loads all configs)
RateLimiterManager rateLimiter; 

void handleRequest(const Request& req) {
    std::string userId = req.userId;
    std::string tier = req.userTier; // e.g., "FREE"

    // One-line check
    if (rateLimiter.allowRequest(userId, tier)) {
        // ... Process Request ...
    } else {
        // ... Return 429 Too Many Requests ...
    }
}
```

## 📂 Project Structure

-   `src/service/RateLimiterManager.cpp`: Facade for the entire system.
-   `src/config/`: Configuration parsers.
-   `src/limiter/`: Algorithm implementations.
-   `src/main.cpp`: Demo application showing usage.
