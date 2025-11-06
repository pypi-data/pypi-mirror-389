"""
TypedDict response models for Google Docs tools.

These models define the structure of responses returned by Google Docs tools,
with field descriptions as string literals for tool compatibility.
"""

from typing import TypedDict


class TabMetadata(TypedDict, total=False):
    """Metadata for a single tab in a Google Docs document."""

    tabId: str
    """The unique identifier of the tab."""

    title: str
    """The title/name of the tab."""

    index: int
    """The position of the tab among its siblings (0-indexed)."""

    nestingLevel: int
    """The nesting depth (0 for top-level, 1 for child, 2 for grandchild)."""

    approximateCharacterCount: int
    """Approximate number of characters in this tab's content (excluding child tabs)."""

    approximateWordCount: int
    """Approximate number of words in this tab's content (excluding child tabs)."""

    parentTabId: str
    """The ID of the parent tab (if this is a nested tab)."""

    childTabs: list[dict]
    """List of nested child tabs within this tab (each follows TabMetadata structure)."""


class DocumentMetadata(TypedDict):
    """Complete metadata for a Google Docs document including tab hierarchy."""

    documentId: str
    """The unique identifier of the document."""

    title: str
    """The title of the document."""

    documentUrl: str
    """The URL to open and edit the document in Google Docs."""

    approximateTotalCharacterCount: int
    """Approximate total number of characters across all tabs (or main body if no tabs)."""

    approximateTotalWordCount: int
    """Approximate total number of words across all tabs (or main body if no tabs)."""

    tabsCount: int
    """The total number of tabs in the document."""

    tabs: list[dict]
    """List of tabs with hierarchical structure (each follows TabMetadata structure)."""


class DocumentContentResult(TypedDict):
    """A document with its content in a specific format and metadata."""

    documentId: str
    """The unique identifier of the document."""

    title: str
    """The title of the document."""

    documentUrl: str
    """The URL to open and edit the document in Google Docs."""

    content: str
    """The document content in the requested format (markdown, HTML, or DocMD)."""

    format: str
    """The format of the content: 'markdown', 'html', 'docmd', or 'google_api_json'."""

    tabs_count: int
    """The number of tabs in the document (0 if no tabs)."""

    total_character_count: int
    """Approximate total character count across all tabs or main body if no tabs."""

    total_word_count: int
    """Approximate total word count across all tabs or main body if no tabs."""

    main_body_character_count: int
    """Approximate character count of the main body content only (0 if document has tabs)."""

    main_body_word_count: int
    """Approximate word count of the main body content only (0 if document has tabs)."""


class DocumentListItem(TypedDict):
    """Metadata for a document from search results."""

    id: str
    """The unique identifier of the document."""

    name: str
    """The name/title of the document."""

    kind: str
    """The kind of the resource (typically 'drive#file')."""

    mimeType: str
    """The MIME type (typically 'application/vnd.google-apps.document')."""


class SearchDocumentsResponse(TypedDict, total=False):
    """Response from search_documents with document metadata and pagination."""

    documents_count: int
    """The number of documents returned in this response."""

    documents: list[dict]
    """List of document metadata matching search criteria."""

    pagination_token: str
    """Token to retrieve the next page of results (if available)."""

    has_more: bool
    """Whether there are more documents available to retrieve."""


class SearchAndRetrieveResponse(TypedDict, total=False):
    """Response from search_and_retrieve_documents with full content and metadata."""

    documents_count: int
    """The number of documents returned in this response."""

    documents: list[dict]
    """List of documents with their content and metadata."""

    pagination_token: str
    """Token to retrieve the next page of results (if available)."""

    has_more: bool
    """Whether there are more documents available to retrieve."""
