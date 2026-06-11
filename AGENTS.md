# Klaaro Python SDK — Agent Reference

## Package

- **name**: `klaaro`
- **version**: `0.1.0`
- **import**: `from klaaro import KlaaroClient, AsyncKlaaroClient`
- **runtime**: Python 3.9+
- **deps**: `httpx>=0.27`, `pydantic>=2`

## Constructors

```python
KlaaroClient(
    api_key: str | None = None,   # falls back to KLAARO_API_KEY env var
    base_url: str = "https://klaaro.ai/api/v1",
    timeout: float = 30.0,
)

AsyncKlaaroClient(
    api_key: str | None = None,
    base_url: str = "https://klaaro.ai/api/v1",
    timeout: float = 30.0,
)
```

Dev base URL: `"https://dev.klaaro.ai/api/v1"`
Env var: `KLAARO_API_KEY`

Both support context managers (`with` / `async with`). Call `client.close()` / `await client.aclose()` to release the underlying httpx connection pool.

## Authentication

All requests: `Authorization: Bearer <api_key>`
Scopes: `read` (GET), `write` (POST/DELETE), `export` (export endpoints)
Obtain key: dashboard → Team → API keys

## Error class

```python
class KlaaroAPIError(KlaaroError):
    status: int
    code: str
    message: str
    param: str | None
    request_id: str | None
```

## Rate-limit response headers

| Header                  | Meaning                              |
| ----------------------- | ------------------------------------ |
| `X-RateLimit-Limit`     | Requests allowed per window          |
| `X-RateLimit-Remaining` | Requests left in current window      |
| `X-RateLimit-Reset`     | Unix timestamp when window resets    |
| `Retry-After`           | Seconds to wait (429 responses only) |
| `X-Request-Id`          | Echoed on every response             |

## Paginated return type

All list methods return `tuple[list[T], ListMeta]`.

```python
class ListMeta(BaseModel):
    next_cursor: str | None   # alias: nextCursor
    has_more: bool            # alias: hasMore
```

Params: `limit: int | None` (1–200, default 50), `cursor: str | None`

## Methods — sync (`KlaaroClient`) and async (`AsyncKlaaroClient`, prepend `await`)

### Datasets

| Method | HTTP | Path | Key params | Returns |
|--------|------|------|------------|---------|
| `list_datasets(*, limit, cursor)` | GET | `/datasets` | — | `tuple[list[Dataset], ListMeta]` |
| `get_dataset(dataset_id)` | GET | `/datasets/{id}` | — | `Dataset` |
| `delete_dataset(dataset_id)` | DELETE | `/datasets/{id}` | — | `None` (204) |
| `list_dataset_records(dataset_id, *, limit, cursor, class_, approval, created_after, created_before)` | GET | `/datasets/{id}/records` | — | `tuple[list[RecordClean], ListMeta]` |
| `list_dataset_records_flat(dataset_id, ...)` | GET | `/datasets/{id}/records-flat` | same | `tuple[list[Record], ListMeta]` |
| `list_dataset_records_nested(dataset_id, ...)` | GET | `/datasets/{id}/records-nested` | same | `tuple[list[RecordNested], ListMeta]` |
| `list_dataset_classes(dataset_id)` | GET | `/datasets/{id}/classes` | — | `tuple[list[Class], ListMeta]` |
| `get_dataset_class(dataset_id, class_slug)` | GET | `/datasets/{id}/classes/{slug}` | — | `Class` |
| `list_approval_queue(dataset_id, *, limit, cursor, status)` | GET | `/datasets/{id}/approval-queue` | — | `tuple[list[ApprovalQueueItem], ListMeta]` |

### Documents

| Method | HTTP | Path | Key params | Returns |
|--------|------|------|------------|---------|
| `list_documents(*, dataset_id, limit, cursor, class_, status, created_after, created_before)` | GET | `/documents` | — | `tuple[list[Document], ListMeta]` |
| `upload_document(dataset_id, *, file, filename, url, fixed_class, idempotency_key, replace_document_id)` | POST | `/documents` | file XOR url | `Document` (201) |
| `get_document(document_id)` | GET | `/documents/{id}` | — | `Document` |
| `delete_document(document_id)` | DELETE | `/documents/{id}` | — | `None` (204) |
| `rerun_document(document_id, *, from_step, fixed_class)` | POST | `/documents/{id}/rerun` | — | `Document` |
| `get_document_records(document_id, *, include_unapproved)` | GET | `/documents/{id}/records` | — | `DocumentRecordsResponse` |
| `get_document_records_flat(document_id, *, include_unapproved)` | GET | `/documents/{id}/records-flat` | — | `DocumentRecordsFlatResponse` |
| `get_document_records_nested(document_id, *, include_unapproved)` | GET | `/documents/{id}/records-nested` | — | `DocumentRecordsNestedResponse` |

`upload_document` notes:
- `file`: `IO[bytes]`, `bytes`, or `pathlib.Path`. Mutually exclusive with `url`.
- `idempotency_key` sends `Idempotency-Key` header; replay returns `Idempotency-Replay: true` response header.
- `fixed_class`: forces a specific class slug.

### Records

| Method | HTTP | Path | Key params | Returns |
|--------|------|------|------------|---------|
| `get_record(record_id)` | GET | `/records/{id}` | — | `RecordClean` |
| `get_record_flat(record_id)` | GET | `/records-flat/{id}` | — | `Record` |
| `get_record_nested(record_id)` | GET | `/records-nested/{id}` | — | `RecordNested` |
| `list_record_field_events(record_id, *, field_path, kinds, limit, cursor)` | GET | `/records/{id}/field-events` | — | `tuple[list[FieldEvent], ListMeta]` |
| `get_record_comments(record_id)` | GET | `/records/{id}/comments` | — | `tuple[list[CommentView], ListMeta]` |
| `get_record_approvals(record_id)` | GET | `/records/{id}/approvals` | — | `tuple[list[ApprovalEvent], ListMeta]` |

### Webhooks

| Method | HTTP | Path | Key params | Returns |
|--------|------|------|------------|---------|
| `list_webhooks(dataset_id, *, limit, cursor)` | GET | `/webhooks` | — | `tuple[list[Webhook], ListMeta]` |
| `create_webhook(dataset_id, url, events, *, description)` | POST | `/webhooks` | — | `Webhook` (201) |
| `update_webhook(webhook_id, dataset_id, *, url, events, description)` | PATCH | `/webhooks/{id}` | — | `Webhook` |
| `delete_webhook(webhook_id, dataset_id)` | DELETE | `/webhooks/{id}` | — | `None` (204) |
| `rotate_webhook_secret(webhook_id, dataset_id)` | POST | `/webhooks/{id}/rotate-secret` | — | `str` (new secret) |

### Misc

| Method | HTTP | Path | Auth | Returns |
|--------|------|------|------|---------|
| `get_openapi_spec()` | GET | `/openapi` | none | `Any` (raw dict) |

## Key model attributes (snake_case, Pydantic v2)

```python
# Dataset
id, slug, name, description, document_count, created_at, updated_at

# Document
id, dataset_id, dataset_slug, filename, file_type, file_size,
status, current_step, class_, error, pipeline, created_at, updated_at
# status: "queued" | "processing" | "completed" | "failed" | "cancelled"

# RecordClean — pure extracted values
id, document_id, class_, data: dict[str, Any]

# Record — flat FieldView map
id, document_id, dataset_id, ..., fields: dict[str, FieldView]

# RecordNested — FieldView at each leaf
id, document_id, dataset_id, ..., data: Any

# DocumentRecordsResponse
records: list[RecordClean], class_: DocumentClassSummary

# Webhook
id, url, events, description, secret_last4, last_delivery_at, created_at
```

## Webhook events

```python
WEBHOOK_EVENTS = (
    "document.ocr_completed",
    "document.extraction_completed",
    "document.failed",
    "document.uploaded",
    "record.updated",
    "record.approved",
    "evaluation.completed",
)
```

## Error codes

| Code | Status |
|------|--------|
| `not_authenticated` | 401 |
| `api_key_required` | 401 |
| `insufficient_scope` | 403 |
| `dataset_not_found` | 404 |
| `document_not_found` | 404 |
| `record_not_found` | 404 |
| `webhook_not_found` | 404 |
| `class_not_found` | 404 |
| `validation_error` | 400 |
| `business_rule_violation` | 422 |
| `rate_limited` | 429 |
| `idempotency_conflict` | 409 |
| `internal_error` | 500 |
