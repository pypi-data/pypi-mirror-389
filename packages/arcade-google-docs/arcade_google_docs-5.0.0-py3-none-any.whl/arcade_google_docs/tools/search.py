from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_docs.enum import DocumentFormat, OrderBy
from arcade_google_docs.models.document import Document
from arcade_google_docs.models.responses import (
    SearchAndRetrieveResponse,
    SearchDocumentsResponse,
)
from arcade_google_docs.tools import get_document_by_id
from arcade_google_docs.utils import (
    build_document_content_result,
    build_drive_service,
    build_files_list_params,
    build_search_retrieve_response,
)


# Implements: https://googleapis.github.io/google-api-python-client/docs/dyn/drive_v3.files.html#list
# Example `arcade chat` query: `list my 5 most recently modified documents`
# TODO: Support query with natural language. Currently, the tool expects a fully formed query
#       string as input with the syntax defined here: https://developers.google.com/drive/api/guides/search-files
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def search_documents(
    context: ToolContext,
    document_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    document_not_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must NOT be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    search_only_in_shared_drive_id: Annotated[
        str | None,
        "The ID of the shared drive to restrict the search to. If provided, the search will only "
        "return documents from this drive. Defaults to None, which searches across all drives.",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "Whether to include documents from shared drives. Defaults to False (searches only in "
        "the user's 'My Drive').",
    ] = False,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified documents first. If "
        "document_contains or document_not_contains is provided, "
        "then the order_by will be ignored.",
    ] = None,
    limit: Annotated[int, "The number of documents to list"] = 50,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    SearchDocumentsResponse,
    "Document count, list of documents, pagination token, and has_more flag",
]:
    """
    Searches for documents in the user's Google Drive. Excludes documents in trash.
    Returns metadata only. Use get_document_metadata or get_document_as_docmd for content.
    """
    if document_contains or document_not_contains:
        # Google drive API does not support other order_by values for
        # queries with fullText search (which is used when document_contains
        # or document_not_contains is provided).
        order_by = None
    elif order_by is None:
        order_by = [OrderBy.MODIFIED_TIME_DESC]
    elif isinstance(order_by, OrderBy):
        order_by = [order_by]

    page_size = min(10, limit)
    files: list[dict[str, Any]] = []

    service = build_drive_service(context.get_auth_token_or_empty())

    params = build_files_list_params(
        mime_type="application/vnd.google-apps.document",
        document_contains=document_contains,
        document_not_contains=document_not_contains,
        page_size=page_size,
        order_by=order_by,
        pagination_token=pagination_token,
        include_shared_drives=include_shared_drives,
        search_only_in_shared_drive_id=search_only_in_shared_drive_id,
        include_organization_domain_documents=include_organization_domain_documents,
    )

    while len(files) < limit:
        if pagination_token:
            params["pageToken"] = pagination_token
        else:
            params.pop("pageToken", None)

        results = service.files().list(**params).execute()
        batch = results.get("files", [])
        files.extend(batch[: limit - len(files)])

        pagination_token = results.get("nextPageToken")
        if not pagination_token or len(batch) < page_size:
            break

    response_dict: dict = {
        "documents_count": len(files),
        "documents": files,
        "has_more": pagination_token is not None,
    }

    if pagination_token:
        response_dict["pagination_token"] = pagination_token

    return response_dict  # type: ignore[return-value]


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def search_and_retrieve_documents(
    context: ToolContext,
    return_format: Annotated[
        DocumentFormat,
        "The format of the document to return. Defaults to Markdown.",
    ] = DocumentFormat.MARKDOWN,
    document_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    document_not_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must NOT be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    search_only_in_shared_drive_id: Annotated[
        str | None,
        "The ID of the shared drive to restrict the search to. If provided, the search will only "
        "return documents from this drive. Defaults to None, which searches across all drives.",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "Whether to include documents from shared drives. Defaults to False (searches only in "
        "the user's 'My Drive').",
    ] = False,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = None,
    limit: Annotated[int, "The number of documents to list"] = 50,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    SearchAndRetrieveResponse,
    "A dictionary containing document count, list of documents with content and metadata, "
    "pagination token, and has_more flag",
]:
    """
    Searches for documents in the user's Google Drive and returns documents with their main body
    content and tab metadata. Excludes documents that are in the trash.

    Returns main body content only with metadata about tabs. Use get_document_as_docmd() to retrieve
    full tab content for specific documents. Use search_documents() for metadata-only searches.
    """
    search_response = await search_documents(
        context=context,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
        search_only_in_shared_drive_id=search_only_in_shared_drive_id,
        include_shared_drives=include_shared_drives,
        include_organization_domain_documents=include_organization_domain_documents,
        order_by=order_by,
        limit=limit,
        pagination_token=pagination_token,
    )

    documents: list = []
    for item in search_response["documents"]:
        doc_dict = await get_document_by_id(context, document_id=item["id"])
        document = Document(**doc_dict)
        doc_result = build_document_content_result(document, doc_dict, return_format)
        documents.append(doc_result)

    result = build_search_retrieve_response(documents, search_response)
    return result  # type: ignore[return-value]
