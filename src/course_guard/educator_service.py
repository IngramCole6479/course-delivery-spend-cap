from fastapi import FastAPI, HTTPException
from openai import APIStatusError

from .course_delivery import deliver_course_request
from .infrai_gateway import InfraiError, InfraiGateway
from .request_models import CourseDeliveryRequest, CourseDeliveryResult

app = FastAPI(title="Course delivery spend guard")


@app.post("/course-deliveries", response_model=CourseDeliveryResult)
def create_course_delivery(request: CourseDeliveryRequest) -> CourseDeliveryResult:
    try:
        return deliver_course_request(request, InfraiGateway())
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except APIStatusError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": "chat_api_error", "message": str(exc)},
        ) from exc
