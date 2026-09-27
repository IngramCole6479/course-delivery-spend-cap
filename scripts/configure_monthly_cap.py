import argparse

from course_guard.infrai_gateway import InfraiGateway


def main() -> None:
    parser = argparse.ArgumentParser(description="Set the account monthly hard cap")
    parser.add_argument("hard_cap_usd", type=float)
    parser.add_argument("--alert-threshold-usd", type=float)
    args = parser.parse_args()

    result = InfraiGateway().set_monthly_cap(
        hard_cap_usd=args.hard_cap_usd,
        alert_threshold_usd=args.alert_threshold_usd,
    )
    print(f"Monthly hard cap configured: {result}")


if __name__ == "__main__":
    main()
