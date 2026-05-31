"""Pydantic v2 models mirroring the Klaaro /api/v1 response shapes.

API fields are camelCase; model attributes are snake_case.
`model_config = ConfigDict(populate_by_name=True)` allows either form.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared / pagination
# ---------------------------------------------------------------------------


class ListMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class ListResponse[T](BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: list[T]
    meta: ListMeta


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class Dataset(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    slug: str
    name: str
    description: str
    document_count: int = Field(alias="documentCount")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class SchemaField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    type: str
    description: Optional[str] = None
    required: bool
    children: Optional[list["SchemaField"]] = None
    array_item_type: Optional[str] = Field(None, alias="arrayItemType")
    array_item_fields: Optional[list["SchemaField"]] = Field(None, alias="arrayItemFields")
    enum_values: Optional[list[str | int]] = Field(None, alias="enumValues")


SchemaField.model_rebuild()


class Class(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    description: str
    color: str
    schema_hash: str = Field(alias="schemaHash")
    class_hash: str = Field(alias="classHash")
    fields: list[SchemaField]
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

DocumentStatus = Literal["queued", "processing", "completed", "failed", "cancelled"]


class DocumentClassRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: Optional[str] = None
    name: Optional[str] = None


class PipelineStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    last_run_id: Optional[str] = Field(None, alias="lastRunId")
    last_finished_at: Optional[str] = Field(None, alias="lastFinishedAt")
    from_step: Optional[str] = Field(None, alias="fromStep")


class Document(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    dataset_id: str = Field(alias="datasetId")
    dataset_slug: str = Field(alias="datasetSlug")
    filename: str
    file_type: str = Field(alias="fileType")
    file_size: int = Field(alias="fileSize")
    status: DocumentStatus
    current_step: str = Field(alias="currentStep")
    class_: DocumentClassRef = Field(alias="class")
    error: Optional[str] = None
    ingest_source_display: Optional[str] = Field(None, alias="ingestSourceDisplay")
    pipeline: PipelineStatus
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


# ---------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------

ApprovalStatus = Literal["pending", "approved", "approved_with_changes", "rejected"]
FieldAnnotationKind = Literal["corrected_unsure", "confirmed_unsure", "edited_unflagged", "reviewed_unchanged"]
FieldAnnotationTier = Literal["bronze", "silver", "gold"]
FieldActorKind = Literal["user", "api_key", "model", "system"]


class RecordClassRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: Optional[str] = None
    name: Optional[str] = None
    schema_hash: Optional[str] = Field(None, alias="schemaHash")
    class_hash: Optional[str] = Field(None, alias="classHash")


class FieldAnnotation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: FieldAnnotationKind
    tier: FieldAnnotationTier
    reviewer_id: Optional[str] = Field(None, alias="reviewerId")
    created_at: str = Field(alias="createdAt")


class FieldActor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: FieldActorKind
    id: Optional[str] = None
    name: Optional[str] = None


class FieldReview(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latest_annotation: Optional[FieldAnnotation] = Field(None, alias="latestAnnotation")
    is_unsure: bool = Field(alias="isUnsure")
    open_flag_id: Optional[str] = Field(None, alias="openFlagId")
    comment_count: int = Field(alias="commentCount")
    event_count: int = Field(alias="eventCount")
    last_actor: Optional[FieldActor] = Field(None, alias="lastActor")
    last_at: Optional[str] = Field(None, alias="lastAt")


class Violation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rule_id: str = Field(alias="ruleId")
    rule_kind: str = Field(alias="ruleKind")
    severity: Literal["soft", "hard"]
    status: Literal["fail", "error"]
    message: str
    details: Optional[dict[str, Any]] = None


class FieldValidation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    violations: list[Violation]
    has_hard: bool = Field(alias="hasHard")


class FieldExtraction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    evidence: Optional[str] = None
    model_unsure: bool = Field(alias="modelUnsure")
    model_note: Optional[str] = Field(None, alias="modelNote")


class FieldSchemaInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    required: bool
    description: Optional[str] = None
    enum_values: Optional[list[str | int]] = Field(None, alias="enumValues")


class FieldScores(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    self_consistency: Optional[float] = Field(None, alias="selfConsistency")
    evidence_coverage: Optional[float] = Field(None, alias="evidenceCoverage")
    schema_conformance: Optional[float] = Field(None, alias="schemaConformance")
    judge_score: Optional[float] = Field(None, alias="judgeScore")
    truth_match: Optional[bool] = Field(None, alias="truthMatch")


class FieldView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    field_root: str = Field(alias="fieldRoot")
    value: Any = None
    schema_info: Optional[FieldSchemaInfo] = Field(None, alias="schema")
    extraction: FieldExtraction
    review: FieldReview
    validation: FieldValidation
    scores: Optional[FieldScores] = None


class ApprovalView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Optional[ApprovalStatus] = None
    triggered_by: list[str] = Field(alias="triggeredBy")


class QualitySubScores(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    null: Optional[float] = None
    unsure: Optional[float] = None
    validation: Optional[float] = None
    self_consistency: Optional[float] = Field(None, alias="selfConsistency")
    judge: Optional[float] = None


class QualityView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kqs: Optional[float] = None
    sub_scores: Optional[QualitySubScores] = Field(None, alias="subScores")
    truth_score: Optional[float] = Field(None, alias="truthScore")
    schema_hash: Optional[str] = Field(None, alias="schemaHash")
    computed_at: Optional[str] = Field(None, alias="computedAt")


class CommentAuthor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["user", "api_key"]
    id: Optional[str] = None
    name: Optional[str] = None


class CommentView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    body: str
    author: CommentAuthor
    created_at: str = Field(alias="createdAt")


class CrossFieldValidation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    validation: FieldValidation


class RecordComments(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    count: int
    preview: list[CommentView]


class Record(BaseModel):
    """Flat record with FieldView map (records / records-flat endpoints)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    document_id: str = Field(alias="documentId")
    dataset_id: str = Field(alias="datasetId")
    dataset_slug: str = Field(alias="datasetSlug")
    row_index: int = Field(alias="rowIndex")
    class_: RecordClassRef = Field(alias="class")
    source_page: Optional[int] = Field(None, alias="sourcePage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    approval: Optional[ApprovalView] = None
    quality: Optional[QualityView] = None
    fields: dict[str, FieldView]
    cross_field: CrossFieldValidation = Field(alias="crossField")
    comments: RecordComments


class RecordNested(BaseModel):
    """Nested record with FieldView tree (records-nested endpoints)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    document_id: str = Field(alias="documentId")
    dataset_id: str = Field(alias="datasetId")
    dataset_slug: str = Field(alias="datasetSlug")
    row_index: int = Field(alias="rowIndex")
    class_: RecordClassRef = Field(alias="class")
    source_page: Optional[int] = Field(None, alias="sourcePage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    approval: Optional[ApprovalView] = None
    quality: Optional[QualityView] = None
    data: Any = None
    cross_field: CrossFieldValidation = Field(alias="crossField")
    comments: RecordComments


class RecordClean(BaseModel):
    """Pure extracted values, no FieldView wrappers (records endpoint)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    document_id: str = Field(alias="documentId")
    class_: RecordClassRef = Field(alias="class")
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------

ApprovalEventAction = Literal[
    "created_pending",
    "auto_approved",
    "approved",
    "approved_with_changes",
    "rejected",
    "reset_to_pending",
]


class ApprovalActor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["user", "api_key", "system"]
    id: Optional[str] = None
    name: Optional[str] = None


class ApprovalEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    action: ApprovalEventAction
    actor: ApprovalActor
    comment: Optional[str] = None
    created_at: str = Field(alias="createdAt")


class ApprovalQueueItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    record_id: str = Field(alias="recordId")
    document_id: str = Field(alias="documentId")
    document_filename: str = Field(alias="documentFilename")
    classification: Optional[str] = None
    status: ApprovalStatus
    triggered_by: list[str] = Field(alias="triggeredBy")
    assigned_reviewer_id: Optional[str] = Field(None, alias="assignedReviewerId")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


# ---------------------------------------------------------------------------
# Field events
# ---------------------------------------------------------------------------


class FieldEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    field_path: str = Field(alias="fieldPath")
    kind: str
    body: Optional[str] = None
    prior_value: Any = Field(None, alias="priorValue")
    new_value: Any = Field(None, alias="newValue")
    actor: FieldActor
    created_at: str = Field(alias="createdAt")


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

WebhookEvent = Literal[
    "document.ocr_completed",
    "document.extraction_completed",
    "document.failed",
    "document.uploaded",
    "record.updated",
    "record.approved",
    "evaluation.completed",
]

WEBHOOK_EVENTS: tuple[WebhookEvent, ...] = (
    "document.ocr_completed",
    "document.extraction_completed",
    "document.failed",
    "document.uploaded",
    "record.updated",
    "record.approved",
    "evaluation.completed",
)


class Webhook(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    events: list[WebhookEvent]
    description: Optional[str] = None
    secret_last4: Optional[str] = Field(None, alias="secretLast4")
    last_delivery_at: Optional[str] = Field(None, alias="lastDeliveryAt")
    last_status: Optional[str] = Field(None, alias="lastStatus")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


# ---------------------------------------------------------------------------
# Document records response
# ---------------------------------------------------------------------------


class DocumentClassSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: Optional[str] = None
    name: Optional[str] = None


class DocumentRecordsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[RecordClean]
    class_: DocumentClassSummary = Field(alias="class")


class DocumentRecordsFlatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[Record]
    class_: DocumentClassSummary = Field(alias="class")


class DocumentRecordsNestedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[RecordNested]
    class_: DocumentClassSummary = Field(alias="class")
