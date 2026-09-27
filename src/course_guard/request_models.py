from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseDeliveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: str = Field(min_length=1, max_length=80)
    learner_id: str = Field(min_length=1, max_length=80)
    lesson_prompt: str = Field(min_length=1, max_length=4000)
    learner_deadline: datetime
    educator_report: bool = False


class CourseDeliveryResult(BaseModel):
    course_id: str
    learner_id: str
    lane: str
    answer: str
