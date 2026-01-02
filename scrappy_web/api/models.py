from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid

class ScrapMode(str, Enum):
    WORD_FREQUENCY = "word-frequency"
    FULL = "full"
    METADATA = "metadata"
    ENTROPY = "entropy"

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    mode: ScrapMode
    filename: str

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    output: List[str] = []
    error: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
