from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class DeliveryLane(StrEnum):
    DEADLINE = "deadline"
    STANDARD = "standard"
    REPORTING = "reporting"


@dataclass(frozen=True)
class DeliveryDecision:
    lane: DeliveryLane
    response_words: int


def choose_delivery_lane(
    *, learner_deadline: datetime, educator_report: bool, now: datetime
) -> DeliveryDecision:
    """Choose a bounded response shape before making the metered call."""
    if learner_deadline.tzinfo is None or now.tzinfo is None:
        raise ValueError("learner_deadline and now must include a timezone")

    hours_remaining = (learner_deadline - now).total_seconds() / 3600
    if hours_remaining <= 24:
        return DeliveryDecision(DeliveryLane.DEADLINE, 180)
    if educator_report:
        return DeliveryDecision(DeliveryLane.REPORTING, 320)
    return DeliveryDecision(DeliveryLane.STANDARD, 240)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
