from collections.abc import Callable
from datetime import datetime

from .course_policy import choose_delivery_lane, utc_now
from .infrai_gateway import InfraiGateway
from .request_models import CourseDeliveryRequest, CourseDeliveryResult


def deliver_course_request(
    request: CourseDeliveryRequest,
    gateway: InfraiGateway,
    *,
    clock: Callable[[], datetime] = utc_now,
) -> CourseDeliveryResult:
    decision = choose_delivery_lane(
        learner_deadline=request.learner_deadline,
        educator_report=request.educator_report,
        now=clock(),
    )
    answer = gateway.deliver_lesson(
        prompt=request.lesson_prompt,
        response_words=decision.response_words,
    )
    return CourseDeliveryResult(
        course_id=request.course_id,
        learner_id=request.learner_id,
        lane=decision.lane,
        answer=answer,
    )
