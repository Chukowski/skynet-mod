import time
from enum import Enum

from pydantic import BaseModel, computed_field, Field

from skynet.modules.ttt.summaries.prompts.action_items import action_items_meeting
from skynet.modules.ttt.summaries.prompts.summary import summary_meeting


class HintType(Enum):
    CONVERSATION = 'conversation'
    EMAILS = 'emails'
    MEETING = 'meeting'
    TEXT = 'text'


class Priority(Enum):
    NORMAL = 'normal'
    HIGH = 'high'


class DocumentPayload(BaseModel):
    text: str
    hint: HintType = HintType.MEETING
    max_tokens: int = None
    priority: Priority = Priority.NORMAL
    prompt: str | None = None


class ActionItemsDocumentPayload(DocumentPayload):
    model_config = {
        'json_schema_extra': {
            'examples': [
                {'text': 'Your text here', 'hint': 'text', 'priority': 'normal', 'prompt': action_items_meeting}
            ]
        }
    }


class SummaryDocumentPayload(DocumentPayload):
    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'text': 'Your text here',
                    'hint': 'meeting',
                    'max_tokens': None,
                    'priority': 'normal',
                    'prompt': summary_meeting,
                }
            ]
        }
    }


class DocumentMetadata(BaseModel):
    app_id: str | None = None
    customer_id: str | None = None


class JobType(Enum):
    ACTION_ITEMS = 'action_items'
    SUMMARY = 'summary'


class Processors(Enum):
    OPENAI = 'OPENAI'
    AZURE = 'AZURE'
    LOCAL = 'LOCAL'


class JobStatus(Enum):
    ERROR = 'error'
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'


# job model to expose to the API
class BaseJob(BaseModel):
    duration: float = 0.0
    id: str
    processor: Processors = Processors.LOCAL
    result: str | None = None
    status: JobStatus = JobStatus.PENDING
    type: JobType


# since private fields are not serialized, use a different model with required internals
class Job(BaseJob):
    created: float = Field(default_factory=time.time)
    end: float | None = None
    metadata: DocumentMetadata = DocumentMetadata()
    payload: DocumentPayload
    start: float | None = None
    worker_id: int | None = None

    @computed_field
    @property
    def computed_duration(self) -> float:
        if self.start and self.end:
            return round(self.end - self.start, 3)

        return 0.0

    @computed_field
    @property
    def computed_full_duration(self) -> float:
        if self.end:
            return round(self.end - self.created, 3)

        return 0.0


class JobId(BaseModel):
    id: str
