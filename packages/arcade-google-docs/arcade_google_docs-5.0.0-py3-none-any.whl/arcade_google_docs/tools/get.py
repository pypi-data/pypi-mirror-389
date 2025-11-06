from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_docs.docmd import build_docmd
from arcade_google_docs.models.document import Document
from arcade_google_docs.models.responses import DocumentMetadata
from arcade_google_docs.utils import (
    _calculate_character_count,
    _calculate_word_count,
    build_docs_service,
    build_tab_metadata_recursive,
    count_tab_chars_recursive,
    count_tab_words_recursive,
)


# Uses https://developers.google.com/docs/api/reference/rest/v1/documents/get
# Example `arcade chat` query: `get document with ID 1234567890`
# Note: Document IDs are returned in the response of the Google Drive's `list_documents` tool
@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
)
async def get_document_by_id(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to retrieve."],
) -> Annotated[dict, "The document contents as a dictionary"]:
    """
    DEPRECATED DO NOT USE THIS TOOL
    Get the latest version of the specified Google Docs document.
    """
    service = build_docs_service(context.get_auth_token_or_empty())

    request = service.documents().get(documentId=document_id, includeTabsContent=True)
    response = request.execute()
    return dict(response)


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
)
async def get_document_as_docmd(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to retrieve."],
    tab_id: Annotated[
        str | None,
        "The ID of a specific tab to retrieve. If provided, returns only content from that tab. "
        "If omitted, returns all tabs in sequential depth-first order.",
    ] = None,
) -> Annotated[str, "The document contents as DocMD"]:
    """
    Get the latest version of the specified Google Docs document as DocMD.
    The DocMD output will include tags that can be used to annotate the document with location
    information, the type of block, block IDs, and other metadata. If the document has tabs,
    all tabs are included in sequential order unless a specific tab_id is provided.
    """
    service = build_docs_service(context.get_auth_token_or_empty())

    request = service.documents().get(documentId=document_id, includeTabsContent=True)
    response = request.execute()
    return build_docmd(Document(**response), tab_id=tab_id).to_string()


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
)
async def get_document_metadata(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to get metadata for"],
) -> Annotated[DocumentMetadata, "Document metadata including hierarchical tab structure"]:
    """
    Get metadata for a Google Docs document including hierarchical tab structure.
    Returns document title, ID, URL, total character count, and nested tab information
    with character counts for each tab.
    """
    service = build_docs_service(context.get_auth_token_or_empty())

    request = service.documents().get(documentId=document_id, includeTabsContent=True)
    response = request.execute()
    document = Document(**response)

    total_char_count = 0
    total_word_count = 0
    tabs_metadata: list = []

    if document.tabs and len(document.tabs) > 0:
        tabs_metadata = build_tab_metadata_recursive(document.tabs)
        total_char_count = sum(count_tab_chars_recursive(tab) for tab in tabs_metadata)
        total_word_count = sum(count_tab_words_recursive(tab) for tab in tabs_metadata)
    elif document.body:
        total_char_count = _calculate_character_count(document.body.content)
        total_word_count = _calculate_word_count(document.body.content)

    return {
        "documentId": document.documentId or "",
        "title": document.title or "",
        "documentUrl": f"https://docs.google.com/document/d/{document.documentId}/edit",
        "approximateTotalCharacterCount": total_char_count,
        "approximateTotalWordCount": total_word_count,
        "tabsCount": len(tabs_metadata),
        "tabs": tabs_metadata,
    }
