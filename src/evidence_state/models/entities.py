from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, Enum):
    DOCUMENT = "document"
    WEB = "web"
    API = "api"
    HUMAN = "human"


class ClaimStatus(str, Enum):
    PROPOSED = "proposed"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class VerificationResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class SufficiencyStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTED = "CONFLICTED"
    UNVERIFIABLE = "UNVERIFIABLE"


class Document(BaseModel):
    id: str = Field(default_factory=new_id)
    source_uri: str
    content_hash: str
    source_type: SourceType = SourceType.DOCUMENT
    retrieved_at: datetime = Field(default_factory=now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class Claim(BaseModel):
    id: str = Field(default_factory=new_id)
    text: str
    normalized: str = ""
    claim_type: str = "factual"
    created_at: datetime = Field(default_factory=now)
    status: ClaimStatus = ClaimStatus.PROPOSED
    revision_id: Optional[str] = None


class Evidence(BaseModel):
    id: str = Field(default_factory=new_id)
    claim_id: str
    document_id: str
    quote: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)
    verification_status: VerificationResult = VerificationResult.INCONCLUSIVE


class Verification(BaseModel):
    id: str = Field(default_factory=new_id)
    claim_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    method: str = "structural"
    result: VerificationResult = VerificationResult.INCONCLUSIVE
    explanation: str = ""
    verifier_identity: str = "system"
    timestamp: datetime = Field(default_factory=now)


class Contradiction(BaseModel):
    id: str = Field(default_factory=new_id)
    claim_ids: list[str]
    classification: str = "direct"
    evidence_ids: list[str] = Field(default_factory=list)
    resolution_status: str = "unresolved"
    resolution_provenance: Optional[str] = None


class Revision(BaseModel):
    id: str = Field(default_factory=new_id)
    previous_state_id: Optional[str] = None
    resulting_state_id: str
    changed_entities: list[str] = Field(default_factory=list)
    reason: str = ""
    timestamp: datetime = Field(default_factory=now)
    actor: str = "system"


class Evaluation(BaseModel):
    id: str = Field(default_factory=new_id)
    objective: str
    required_criteria: list[str] = Field(default_factory=list)
    satisfied_criteria: list[str] = Field(default_factory=list)
    unsatisfied_criteria: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    status: SufficiencyStatus = SufficiencyStatus.INSUFFICIENT
    provenance: str = ""


class Policy(BaseModel):
    max_iterations: int = 10
    required_evidence_threshold: int = 1
    mandatory_sources: list[str] = Field(default_factory=list)
    require_verification: bool = True
    require_no_unresolved_contradictions: bool = True
    human_review_required: bool = False
    completion_criteria: list[str] = Field(default_factory=list)