"""Tests for KlaaroClient (sync) using respx to mock httpx."""

from __future__ import annotations

import json
import pytest
import httpx
import respx

from klaaro import KlaaroClient, KlaaroAPIError
from klaaro.models import Dataset, Document, RecordClean, Webhook

BASE = "https://klaaro.ai/api/v1"
FAKE_KEY = "sk_testkey"


def make_client() -> KlaaroClient:
    return KlaaroClient(api_key=FAKE_KEY)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

FAKE_DATASET = {
    "id": "d1d1d1d1-0000-0000-0000-000000000001",
    "slug": "invoices",
    "name": "Invoices",
    "description": "",
    "documentCount": 5,
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z",
}

FAKE_DOC = {
    "id": "doc1doc1-0000-0000-0000-000000000001",
    "datasetId": "d1d1d1d1-0000-0000-0000-000000000001",
    "datasetSlug": "invoices",
    "filename": "invoice.pdf",
    "fileType": "application/pdf",
    "fileSize": 12345,
    "status": "completed",
    "currentStep": "done",
    "class": {"slug": "invoice", "name": "Invoice"},
    "error": None,
    "ingestSourceDisplay": None,
    "pipeline": {"lastRunId": None, "lastFinishedAt": None, "fromStep": None},
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z",
}

FAKE_RECORD = {
    "id": "rec1rec1-0000-0000-0000-000000000001",
    "documentId": "doc1doc1-0000-0000-0000-000000000001",
    "class": {"slug": "invoice", "name": "Invoice", "schemaHash": "abc", "classHash": "def"},
    "data": {"total": 100},
}

FAKE_WEBHOOK = {
    "id": "wh000001-0000-0000-0000-000000000001",
    "url": "https://my.app/hook",
    "events": ["document.extraction_completed"],
    "description": None,
    "secretLast4": "abcd",
    "lastDeliveryAt": None,
    "lastStatus": None,
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z",
}

LIST_META = {"nextCursor": None, "hasMore": False}


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_raises_without_api_key() -> None:
    with pytest.raises(Exception, match="api_key is required"):
        KlaaroClient(api_key="")


def test_accepts_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KLAARO_API_KEY", "sk_from_env")
    client = KlaaroClient()
    assert client._api_key == "sk_from_env"


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


@respx.mock
def test_list_datasets() -> None:
    respx.get(f"{BASE}/datasets").mock(
        return_value=httpx.Response(200, json={"data": [FAKE_DATASET], "meta": LIST_META})
    )
    datasets, meta = make_client().list_datasets(limit=10)
    assert len(datasets) == 1
    assert isinstance(datasets[0], Dataset)
    assert datasets[0].slug == "invoices"
    assert not meta.has_more


@respx.mock
def test_get_dataset() -> None:
    ds_id = FAKE_DATASET["id"]
    respx.get(f"{BASE}/datasets/{ds_id}").mock(
        return_value=httpx.Response(200, json=FAKE_DATASET)
    )
    dataset = make_client().get_dataset(ds_id)
    assert dataset.id == ds_id


@respx.mock
def test_delete_dataset() -> None:
    ds_id = FAKE_DATASET["id"]
    respx.delete(f"{BASE}/datasets/{ds_id}").mock(
        return_value=httpx.Response(204)
    )
    result = make_client().delete_dataset(ds_id)
    assert result is None


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@respx.mock
def test_list_documents() -> None:
    respx.get(f"{BASE}/documents").mock(
        return_value=httpx.Response(200, json={"data": [FAKE_DOC], "meta": LIST_META})
    )
    docs, meta = make_client().list_documents(dataset_id=FAKE_DATASET["id"], status="completed")
    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].status == "completed"


@respx.mock
def test_upload_document_url() -> None:
    respx.post(f"{BASE}/documents").mock(
        return_value=httpx.Response(201, json=FAKE_DOC)
    )
    doc = make_client().upload_document(
        FAKE_DATASET["id"],
        url="https://example.com/invoice.pdf",
    )
    assert isinstance(doc, Document)
    assert doc.id == FAKE_DOC["id"]
    request = respx.calls.last.request
    body = json.loads(request.content)
    assert body["url"] == "https://example.com/invoice.pdf"
    assert request.headers["authorization"] == f"Bearer {FAKE_KEY}"


@respx.mock
def test_upload_document_file_bytes() -> None:
    respx.post(f"{BASE}/documents").mock(
        return_value=httpx.Response(201, json=FAKE_DOC)
    )
    doc = make_client().upload_document(
        FAKE_DATASET["id"],
        file=b"%PDF-1.4 fake content",
        filename="invoice.pdf",
    )
    assert doc.id == FAKE_DOC["id"]
    request = respx.calls.last.request
    assert b"invoice.pdf" in request.content


@respx.mock
def test_upload_document_with_idempotency_key() -> None:
    respx.post(f"{BASE}/documents").mock(
        return_value=httpx.Response(201, json=FAKE_DOC)
    )
    make_client().upload_document(
        FAKE_DATASET["id"],
        url="https://example.com/inv.pdf",
        idempotency_key="my-idem-key",
    )
    request = respx.calls.last.request
    assert request.headers["idempotency-key"] == "my-idem-key"


def test_upload_document_requires_file_or_url() -> None:
    with pytest.raises(Exception, match="provide either file or url"):
        make_client().upload_document(FAKE_DATASET["id"])


@respx.mock
def test_get_document() -> None:
    doc_id = FAKE_DOC["id"]
    respx.get(f"{BASE}/documents/{doc_id}").mock(
        return_value=httpx.Response(200, json=FAKE_DOC)
    )
    doc = make_client().get_document(doc_id)
    assert doc.id == doc_id


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


@respx.mock
def test_get_record() -> None:
    rec_id = FAKE_RECORD["id"]
    respx.get(f"{BASE}/records/{rec_id}").mock(
        return_value=httpx.Response(200, json=FAKE_RECORD)
    )
    record = make_client().get_record(rec_id)
    assert isinstance(record, RecordClean)
    assert record.id == rec_id
    assert record.data["total"] == 100


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


@respx.mock
def test_create_webhook() -> None:
    respx.post(f"{BASE}/webhooks").mock(
        return_value=httpx.Response(201, json=FAKE_WEBHOOK)
    )
    hook = make_client().create_webhook(
        FAKE_DATASET["id"],
        url="https://my.app/hook",
        events=["document.extraction_completed"],
    )
    assert isinstance(hook, Webhook)
    assert hook.id == FAKE_WEBHOOK["id"]


@respx.mock
def test_delete_webhook() -> None:
    hook_id = FAKE_WEBHOOK["id"]
    respx.delete(f"{BASE}/webhooks/{hook_id}").mock(
        return_value=httpx.Response(204)
    )
    result = make_client().delete_webhook(hook_id, FAKE_DATASET["id"])
    assert result is None


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@respx.mock
def test_raises_klaaro_api_error_on_404() -> None:
    doc_id = "missing-id"
    respx.get(f"{BASE}/documents/{doc_id}").mock(
        return_value=httpx.Response(
            404,
            json={
                "error": {
                    "code": "document_not_found",
                    "message": "Document not found",
                    "requestId": "req-abc",
                }
            },
        )
    )
    with pytest.raises(KlaaroAPIError) as exc_info:
        make_client().get_document(doc_id)
    err = exc_info.value
    assert err.status == 404
    assert err.code == "document_not_found"
    assert err.request_id == "req-abc"


@respx.mock
def test_raises_on_401() -> None:
    respx.get(f"{BASE}/datasets").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"code": "not_authenticated", "message": "Authentication required."}},
        )
    )
    with pytest.raises(KlaaroAPIError) as exc_info:
        make_client().list_datasets()
    assert exc_info.value.status == 401
    assert exc_info.value.code == "not_authenticated"


@respx.mock
def test_get_openapi_spec_no_auth() -> None:
    respx.get(f"{BASE}/openapi").mock(
        return_value=httpx.Response(200, json={"openapi": "3.1.0"})
    )
    make_client().get_openapi_spec()
    request = respx.calls.last.request
    assert "authorization" not in request.headers


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_async_list_datasets() -> None:
    from klaaro import AsyncKlaaroClient

    respx.get(f"{BASE}/datasets").mock(
        return_value=httpx.Response(200, json={"data": [FAKE_DATASET], "meta": LIST_META})
    )
    async with AsyncKlaaroClient(api_key=FAKE_KEY) as client:
        datasets, meta = await client.list_datasets()
    assert len(datasets) == 1
    assert datasets[0].slug == "invoices"


@pytest.mark.asyncio
@respx.mock
async def test_async_upload_document_url() -> None:
    from klaaro import AsyncKlaaroClient

    respx.post(f"{BASE}/documents").mock(
        return_value=httpx.Response(201, json=FAKE_DOC)
    )
    async with AsyncKlaaroClient(api_key=FAKE_KEY) as client:
        doc = await client.upload_document(
            FAKE_DATASET["id"],
            url="https://example.com/invoice.pdf",
        )
    assert doc.id == FAKE_DOC["id"]


@pytest.mark.asyncio
@respx.mock
async def test_async_raises_api_error() -> None:
    from klaaro import AsyncKlaaroClient

    respx.get(f"{BASE}/documents/x").mock(
        return_value=httpx.Response(
            404,
            json={"error": {"code": "document_not_found", "message": "Not found"}},
        )
    )
    with pytest.raises(KlaaroAPIError) as exc_info:
        async with AsyncKlaaroClient(api_key=FAKE_KEY) as client:
            await client.get_document("x")
    assert exc_info.value.status == 404
