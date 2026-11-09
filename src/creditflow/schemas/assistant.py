from pydantic import Field

from creditflow.schemas.common import StrictModel


class AssistantRequest(StrictModel):
    question: str = Field(min_length=3, max_length=2000)
