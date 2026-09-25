import sys
from pathlib import Path

# Ensure project root is in sys.path when running as `python src/main.py`
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.service import RateLimiterManager


def main() -> int:
    try:
        # Auto-loads "config/rate_limit_config.json" and "config/rate_limit_policy.json"
        rate_limiter = RateLimiterManager()

        print("\nRate Limiter Service Started.")
        print("Type 'exit' as userId to quit\n")

        while True:
            try:
                user_id = input("Enter userId: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_id:
                continue

            if user_id == "exit":
                print("Shutting down...")
                break

            try:
                tier_input = input("Enter userType (FREE / PREMIUM): ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            try:
                allowed = rate_limiter.allow_request(user_id, tier_input)
                if allowed:
                    print(" Request ALLOWED\n")
                else:
                    print("Request BLOCKED (rate limit exceeded)\n")
            except Exception as e:
                print(f"Error: {e}\n")

    except Exception as ex:
        print(f"Fatal Startup Error: {ex}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
