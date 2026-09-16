#include <iostream>
#include <string>
#include "service/RateLimiterManager.h"

int main() {
    try {
        // 🔹 ONE CALL TO START (Microservice ready)
        // Auto-loads "config/rate_limit_config.json" and "config/rate_limit_policy.json"
        RateLimiterManager rateLimiter;

        std::cout << "\nRate Limiter Service Started.\n";
        std::cout << "Type 'exit' as userId to quit\n\n";

        // 🔹 Request loop (Simulating incoming Microservice requests)
        while (true) {
            std::string userId;
            std::string tierInput;

            std::cout << "Enter userId: ";
            if (!(std::cin >> userId)) break;

            if (userId == "exit") {
                std::cout << "Shutting down...\n";
                break;
            }

            std::cout << "Enter userType (FREE / PREMIUM): ";
            std::cin >> tierInput;

            try {
                // 🔹 ONE CALL TO CHECK LIMIT
                bool allowed = rateLimiter.allowRequest(userId, tierInput);

                if (allowed) {
                    std::cout << " Request ALLOWED\n\n";
                } else {
                    std::cout << "Request BLOCKED (rate limit exceeded)\n\n";
                }
            } catch (const std::exception& e) {
                std::cout << "Error: " << e.what() << "\n\n";
            }
        }
    }
    catch (const std::exception& ex) {
        std::cerr << "Fatal Startup Error: " << ex.what() << std::endl;
        return 1;
    }

    return 0;
}
