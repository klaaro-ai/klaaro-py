"""Asynchronous Klaaro API client."""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, Any, Literal, Optional

import httpx

from ._base import DEFAULT_BASE_URL, build_headers, build_params, raise_for_response
from .errors import KlaaroError
from .models import (
    ApprovalEvent,
    ApprovalQueueItem,
    Class,
    CommentView,
    Dataset,
    Document,
    DocumentRecordsFlatResponse,
    DocumentRecordsNestedResponse,
    DocumentRecordsResponse,
    FieldEvent,
    ListMeta,
    Record,
    RecordClean,
    RecordNested,
    Webhook,
)

# Reuse the same inline list deserialiser logic
def _list(item_model: type, payload: dict[str, Any]) -> tuple[list[Any], ListMeta]:
    data = [item_model.model_validate(item) for item in payload["data"]]
    meta = ListMeta.model_validate(payload["meta"])
    return data, meta


class AsyncKlaaroClient:
    """Asynchronous client for the Klaaro /api/v1 REST API.

    Usage::

        client = AsyncKlaaroClient(api_key="sk_...")
        datasets, meta = await client.list_datasets()
        await client.aclose()

    Or as an async context manager::

        async with AsyncKlaaroClient(api_key="sk_...") as client:
            doc = await client.get_document("b6d2...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        resolved_key = api_key or os.environ.get("KLAARO_API_KEY", "")
        if not resolved_key:
            raise KlaaroError(
                "api_key is required. Pass it as AsyncKlaaroClient(api_key=...) "
                "or set the KLAARO_API_KEY environment variable."
            )
        self._api_key = resolved_key
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=timeout)

    # ------------------------------------------------------------------
    # Async context-manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AsyncKlaaroClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Core request helper
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
        files: Optional[Any] = None,
        data: Optional[dict[str, Any]] = None,
        no_auth: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        url = self._base_url + path
        headers = build_headers(
            api_key=None if no_auth else self._api_key,
            idempotency_key=idempotency_key,
        )
        response = await self._http.request(
            method,
            url,
            params=build_params(params or {}),
            headers=headers,
            json=json,
            files=files,
            data=data,
        )
        raise_for_response(response)
        if response.status_code == 204:
            return None
        return response.json()

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------

    async def list_datasets(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> tuple[list[Dataset], ListMeta]:
        payload = await self._request("GET", "/datasets", params={"limit": limit, "cursor": cursor})
        return _list(Dataset, payload)

    async def get_dataset(self, dataset_id: str) -> Dataset:
        payload = await self._request("GET", f"/datasets/{dataset_id}")
        return Dataset.model_validate(payload)

    async def delete_dataset(self, dataset_id: str) -> None:
        await self._request("DELETE", f"/datasets/{dataset_id}")

    async def list_dataset_records(
        self,
        dataset_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        class_: Optional[str] = None,
        approval: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ) -> tuple[list[RecordClean], ListMeta]:
        payload = await self._request(
            "GET",
            f"/datasets/{dataset_id}/records",
            params={
                "limit": limit,
                "cursor": cursor,
                "class": class_,
                "approval": approval,
                "createdAfter": created_after,
                "createdBefore": created_before,
            },
        )
        return _list(RecordClean, payload)

    async def list_dataset_records_flat(
        self,
        dataset_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        class_: Optional[str] = None,
        approval: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ) -> tuple[list[Record], ListMeta]:
        payload = await self._request(
            "GET",
            f"/datasets/{dataset_id}/records-flat",
            params={
                "limit": limit,
                "cursor": cursor,
                "class": class_,
                "approval": approval,
                "createdAfter": created_after,
                "createdBefore": created_before,
            },
        )
        return _list(Record, payload)

    async def list_dataset_records_nested(
        self,
        dataset_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        class_: Optional[str] = None,
        approval: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ) -> tuple[list[RecordNested], ListMeta]:
        payload = await self._request(
            "GET",
            f"/datasets/{dataset_id}/records-nested",
            params={
                "limit": limit,
                "cursor": cursor,
                "class": class_,
                "approval": approval,
                "createdAfter": created_after,
                "createdBefore": created_before,
            },
        )
        return _list(RecordNested, payload)

    async def list_dataset_classes(self, dataset_id: str) -> tuple[list[Class], ListMeta]:
        payload = await self._request("GET", f"/datasets/{dataset_id}/classes")
        return _list(Class, payload)

    async def get_dataset_class(self, dataset_id: str, class_slug: str) -> Class:
        payload = await self._request("GET", f"/datasets/{dataset_id}/classes/{class_slug}")
        return Class.model_validate(payload)

    async def list_approval_queue(
        self,
        dataset_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[ApprovalQueueItem], ListMeta]:
        payload = await self._request(
            "GET",
            f"/datasets/{dataset_id}/approval-queue",
            params={"limit": limit, "cursor": cursor, "status": status},
        )
        return _list(ApprovalQueueItem, payload)

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def list_documents(
        self,
        *,
        dataset_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        class_: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ) -> tuple[list[Document], ListMeta]:
        payload = await self._request(
            "GET",
            "/documents",
            params={
                "datasetId": dataset_id,
                "limit": limit,
                "cursor": cursor,
                "class": class_,
                "status": status,
                "createdAfter": created_after,
                "createdBefore": created_before,
            },
        )
        return _list(Document, payload)

    async def upload_document(
        self,
        dataset_id: str,
        *,
        file: Optional[IO[bytes] | bytes | Path] = None,
        filename: Optional[str] = None,
        url: Optional[str] = None,
        fixed_class: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        replace_document_id: Optional[str] = None,
    ) -> Document:
        if file is not None:
            resolved_name = filename or (file.name if hasattr(file, "name") else "upload")  # type: ignore[attr-defined]
            if isinstance(file, Path):
                file_bytes = file.read_bytes()
                resolved_name = filename or file.name
            elif isinstance(file, bytes):
                file_bytes = file
            else:
                file_bytes = file.read()

            files = {"file": (resolved_name, file_bytes)}
            form_data: dict[str, Any] = {"datasetId": dataset_id}
            if fixed_class:
                form_data["fixedClassification"] = fixed_class
            if replace_document_id:
                form_data["replaceDocumentId"] = replace_document_id

            payload = await self._request(
                "POST",
                "/documents",
                files=files,
                data=form_data,
                idempotency_key=idempotency_key,
            )
        elif url is not None:
            body: dict[str, Any] = {"datasetId": dataset_id, "url": url}
            if fixed_class:
                body["fixedClass"] = fixed_class
            if idempotency_key:
                body["idempotencyKey"] = idempotency_key
            if replace_document_id:
                body["replaceDocumentId"] = replace_document_id
            payload = await self._request(
                "POST",
                "/documents",
                json=body,
                idempotency_key=idempotency_key,
            )
        else:
            raise KlaaroError("upload_document: provide either file or url")

        return Document.model_validate(payload)

    async def get_document(self, document_id: str) -> Document:
        payload = await self._request("GET", f"/documents/{document_id}")
        return Document.model_validate(payload)

    async def delete_document(self, document_id: str) -> None:
        await self._request("DELETE", f"/documents/{document_id}")

    async def rerun_document(
        self,
        document_id: str,
        *,
        from_step: Optional[Literal["ocr", "classify", "defineClass", "extract"]] = None,
        fixed_class: Optional[str] = None,
    ) -> Document:
        """Re-trigger pipeline processing for an existing document."""
        body: dict[str, str] = {}
        if from_step is not None:
            body["fromStep"] = from_step
        if fixed_class is not None:
            body["fixedClass"] = fixed_class
        payload = await self._request("POST", f"/documents/{document_id}/rerun", json=body)
        return Document.model_validate(payload)

    async def get_document_records(
        self,
        document_id: str,
        *,
        include_unapproved: bool = False,
    ) -> DocumentRecordsResponse:
        payload = await self._request(
            "GET",
            f"/documents/{document_id}/records",
            params={"includeUnapproved": include_unapproved} if include_unapproved else None,
        )
        return DocumentRecordsResponse.model_validate(payload)

    async def get_document_records_flat(
        self,
        document_id: str,
        *,
        include_unapproved: bool = False,
    ) -> DocumentRecordsFlatResponse:
        payload = await self._request(
            "GET",
            f"/documents/{document_id}/records-flat",
            params={"includeUnapproved": include_unapproved} if include_unapproved else None,
        )
        return DocumentRecordsFlatResponse.model_validate(payload)

    async def get_document_records_nested(
        self,
        document_id: str,
        *,
        include_unapproved: bool = False,
    ) -> DocumentRecordsNestedResponse:
        payload = await self._request(
            "GET",
            f"/documents/{document_id}/records-nested",
            params={"includeUnapproved": include_unapproved} if include_unapproved else None,
        )
        return DocumentRecordsNestedResponse.model_validate(payload)

    # ------------------------------------------------------------------
    # Records
    # ------------------------------------------------------------------

    async def get_record(self, record_id: str) -> RecordClean:
        payload = await self._request("GET", f"/records/{record_id}")
        return RecordClean.model_validate(payload)

    async def get_record_flat(self, record_id: str) -> Record:
        payload = await self._request("GET", f"/records-flat/{record_id}")
        return Record.model_validate(payload)

    async def get_record_nested(self, record_id: str) -> RecordNested:
        payload = await self._request("GET", f"/records-nested/{record_id}")
        return RecordNested.model_validate(payload)

    async def list_record_field_events(
        self,
        record_id: str,
        *,
        field_path: Optional[str] = None,
        kinds: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> tuple[list[FieldEvent], ListMeta]:
        payload = await self._request(
            "GET",
            f"/records/{record_id}/field-events",
            params={"fieldPath": field_path, "kinds": kinds, "limit": limit, "cursor": cursor},
        )
        return _list(FieldEvent, payload)

    async def get_record_comments(self, record_id: str) -> tuple[list[CommentView], ListMeta]:
        payload = await self._request("GET", f"/records/{record_id}/comments")
        return _list(CommentView, payload)

    async def get_record_approvals(self, record_id: str) -> tuple[list[ApprovalEvent], ListMeta]:
        payload = await self._request("GET", f"/records/{record_id}/approvals")
        return _list(ApprovalEvent, payload)

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    async def list_webhooks(
        self,
        dataset_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> tuple[list[Webhook], ListMeta]:
        payload = await self._request(
            "GET",
            "/webhooks",
            params={"datasetId": dataset_id, "limit": limit, "cursor": cursor},
        )
        return _list(Webhook, payload)

    async def create_webhook(
        self,
        dataset_id: str,
        url: str,
        events: list[str],
        *,
        description: Optional[str] = None,
    ) -> Webhook:
        body: dict[str, Any] = {"datasetId": dataset_id, "url": url, "events": events}
        if description is not None:
            body["description"] = description
        payload = await self._request("POST", "/webhooks", json=body)
        return Webhook.model_validate(payload)

    async def update_webhook(
        self,
        webhook_id: str,
        dataset_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> Webhook:
        body: dict[str, Any] = {"datasetId": dataset_id}
        if url is not None:
            body["url"] = url
        if events is not None:
            body["events"] = events
        if description is not None:
            body["description"] = description
        payload = await self._request("PATCH", f"/webhooks/{webhook_id}", json=body)
        return Webhook.model_validate(payload)

    async def delete_webhook(self, webhook_id: str, dataset_id: str) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}", json={"datasetId": dataset_id})

    async def rotate_webhook_secret(self, webhook_id: str, dataset_id: str) -> str:
        payload = await self._request(
            "POST",
            f"/webhooks/{webhook_id}/rotate-secret",
            json={"datasetId": dataset_id},
        )
        return payload["secret"]

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    async def get_openapi_spec(self) -> Any:
        """Returns the raw OpenAPI JSON spec. Does not require authentication."""
        return await self._request("GET", "/openapi", no_auth=True)
