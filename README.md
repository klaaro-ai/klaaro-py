# klaaro

Official Python SDK for the [Klaaro](https://klaaro.ai) API — documents in, structured data out.

## Install

```bash
pip install klaaro
```

Requires Python 3.9+. Dependencies: `httpx`, `pydantic>=2`.

## Quick start

```python
from klaaro import KlaaroClient

client = KlaaroClient(api_key="sk_your_key_here")

# 1. List datasets
datasets, meta = client.list_datasets()
print(datasets[0].name)  # "Invoices 2026"

# 2. Upload a document (file)
with open("invoice.pdf", "rb") as f:
    doc = client.upload_document(
        datasets[0].id,
        file=f,
        filename="invoice.pdf",
    )
print(doc.id, doc.status)  # "b6d2a7f6-..." "queued"

# 3. Upload from URL
doc2 = client.upload_document(
    datasets[0].id,
    url="https://example.com/invoice.pdf",
)

# 4. Poll until complete
import time
document = client.get_document(doc.id)
while document.status in ("queued", "processing"):
    time.sleep(3)
    document = client.get_document(doc.id)

# 5. Read extracted records (clean values)
response = client.get_document_records(document.id)
print(response.records[0].data)  # {"vendor_name": "Acme Corp", "total": 1234.56, ...}
```

## Constructor

```python
from klaaro import KlaaroClient

client = KlaaroClient(
    api_key="sk_...",                            # or set KLAARO_API_KEY env var
    base_url="https://dev.klaaro.ai/api/v1",    # optional, defaults to prod
)
```

`api_key` falls back to the `KLAARO_API_KEY` environment variable if not passed.

Get your API key from **Team → API keys** in the Klaaro dashboard.

## Async client

```python
import asyncio
from klaaro import AsyncKlaaroClient

async def main():
    async with AsyncKlaaroClient(api_key="sk_...") as client:
        datasets, meta = await client.list_datasets()
        doc = await client.get_document("b6d2a7f6-...")

asyncio.run(main())
```

## Context manager

```python
with KlaaroClient(api_key="sk_...") as client:
    datasets, meta = client.list_datasets()
```

## Authentication

All requests send `Authorization: Bearer <api_key>`. Three scopes:

| Scope    | Unlocks                     |
| -------- | --------------------------- |
| `read`   | List and get endpoints      |
| `write`  | Upload, create, delete      |
| `export` | Export endpoints            |

## Datasets

```python
# List (paginated) — returns (list[Dataset], ListMeta)
datasets, meta = client.list_datasets(limit=20)

# Get one
dataset = client.get_dataset("a1b2c3d4-...")

# Delete
client.delete_dataset("a1b2c3d4-...")

# Records (clean extracted values)
records, meta = client.list_dataset_records(
    "a1b2c3d4-...",
    class_="invoice",
    approval="approved",
    limit=100,
)

# Records with full field metadata (review, validation, evidence)
flat_records, meta = client.list_dataset_records_flat("a1b2c3d4-...")

# Classes / schemas
classes, meta = client.list_dataset_classes("a1b2c3d4-...")
invoice_class = client.get_dataset_class("a1b2c3d4-...", "invoice")
```

## Documents

```python
# List with filters
docs, meta = client.list_documents(
    dataset_id="a1b2c3d4-...",
    status="completed",
    limit=50,
)

# Upload (idempotent)
from pathlib import Path
doc = client.upload_document(
    "a1b2c3d4-...",
    file=Path("receipt.pdf"),
    idempotency_key="my-unique-key-001",
)

# Get / delete
d = client.get_document("b6d2a7f6-...")
client.delete_document("b6d2a7f6-...")

# Records for a specific document
response = client.get_document_records("b6d2a7f6-...")
flat = client.get_document_records_flat("b6d2a7f6-...", include_unapproved=True)
```

## Records

```python
record = client.get_record("2c0c2e50-...")         # clean values
flat   = client.get_record_flat("2c0c2e50-...")    # flat FieldView map
nested = client.get_record_nested("2c0c2e50-...")  # nested FieldView tree

events, meta  = client.list_record_field_events("2c0c2e50-...", field_path="total")
comments, meta = client.get_record_comments("2c0c2e50-...")
approvals, meta = client.get_record_approvals("2c0c2e50-...")
```

## Webhooks

```python
hook = client.create_webhook(
    "a1b2c3d4-...",
    url="https://my.app/hooks/klaaro",
    events=["document.extraction_completed", "document.failed"],
)

client.update_webhook(hook.id, "a1b2c3d4-...", events=["document.extraction_completed"])

secret = client.rotate_webhook_secret(hook.id, "a1b2c3d4-...")

client.delete_webhook(hook.id, "a1b2c3d4-...")
```

### Webhook signature verification

```python
import hmac
import hashlib
import time

def verify_webhook(raw_body: str, sig_header: str, secret: str) -> bool:
    parts = dict(p.split("=", 1) for p in sig_header.split(","))
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False
    if abs(time.time() - int(timestamp)) > 300:
        return False
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{raw_body}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Pagination

All list methods return `(list[T], ListMeta)`. `ListMeta` has `next_cursor` and `has_more`.

```python
cursor = None
while True:
    records, meta = client.list_dataset_records(
        "a1b2c3d4-...", limit=200, cursor=cursor
    )
    for record in records:
        pass  # process
    if not meta.has_more:
        break
    cursor = meta.next_cursor
```

## Error handling

```python
from klaaro import KlaaroAPIError

try:
    client.get_document("missing-id")
except KlaaroAPIError as e:
    print(e.status, e.code, e.message)
    # 404 document_not_found Document not found
```

| Code                   | Status | Meaning                           |
| ---------------------- | ------ | --------------------------------- |
| `not_authenticated`    | 401    | Missing / invalid API key         |
| `api_key_required`     | 401    | Session auth rejected on v1       |
| `insufficient_scope`   | 403    | Key missing required scope        |
| `dataset_not_found`    | 404    | Dataset not found or inaccessible |
| `document_not_found`   | 404    | Document not found                |
| `record_not_found`     | 404    | Record not found                  |
| `validation_error`     | 400    | Invalid request parameter         |
| `rate_limited`         | 429    | Too many requests                 |
| `internal_error`       | 500    | Unexpected server error           |

## License

MIT
