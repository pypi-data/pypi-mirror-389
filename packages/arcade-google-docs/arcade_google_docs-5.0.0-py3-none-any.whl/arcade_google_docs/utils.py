import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from arcade_google_docs.doc_to_html import convert_document_to_html
from arcade_google_docs.doc_to_markdown import convert_document_to_markdown
from arcade_google_docs.docmd import build_docmd
from arcade_google_docs.enum import Corpora, DocumentFormat, OrderBy
from arcade_google_docs.models.document import StructuralElement

## Set up basic configuration for logging to the console with DEBUG level and a specific format.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def build_docs_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("docs", "v1", credentials=Credentials(auth_token))


def build_drive_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


def build_files_list_params(
    mime_type: str,
    page_size: int,
    order_by: list[OrderBy] | None,
    pagination_token: str | None,
    include_shared_drives: bool,
    search_only_in_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> dict[str, Any]:
    query = build_files_list_query(
        mime_type=mime_type,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
    )

    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": ",".join([item.value for item in order_by]) if order_by else None,
        "pageToken": pagination_token,
    }

    if (
        include_shared_drives
        or search_only_in_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if search_only_in_shared_drive_id:
        params["driveId"] = search_only_in_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    params = remove_none_values(params)

    return params


def build_files_list_query(
    mime_type: str,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> str:
    query = [f"(mimeType = '{mime_type}' and trashed = false)"]

    if isinstance(document_contains, str):
        document_contains = [document_contains]

    if isinstance(document_not_contains, str):
        document_not_contains = [document_not_contains]

    if document_contains:
        for keyword in document_contains:
            name_contains = keyword.replace("'", "\\'")
            full_text_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name contains '{name_contains}' or fullText contains '{full_text_contains}')"
            )
            query.append(keyword_query)

    if document_not_contains:
        for keyword in document_not_contains:
            name_not_contains = keyword.replace("'", "\\'")
            full_text_not_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(not (name contains '{name_not_contains}' or "
                f"fullText contains '{full_text_not_contains}'))"
            )
            query.append(keyword_query)

    return " and ".join(query)


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}


def build_tab_metadata_recursive(
    tabs: list, max_depth: int = 4, current_depth: int = 0
) -> list[Any]:
    """Build hierarchical tab metadata preserving nested structure.

    Args:
        tabs: List of Tab objects with potential childTabs
        max_depth: Maximum recursion depth (Google Docs enforces 3 levels, using 4 for safety)
        current_depth: Current recursion depth

    Returns:
        List of TabMetadata dicts with nested childTabs
    """
    if current_depth >= max_depth:
        return []

    result: list[Any] = []

    for tab in tabs:
        if not tab.tabProperties:
            continue

        char_count = 0
        word_count = 0
        if tab.documentTab and tab.documentTab.body:
            char_count = _calculate_character_count(tab.documentTab.body.content)
            word_count = _calculate_word_count(tab.documentTab.body.content)

        nesting_level = tab.tabProperties.nestingLevel or 0
        if not isinstance(nesting_level, int) or nesting_level < 0:
            nesting_level = 0

        tab_meta_dict: dict = {
            "tabId": tab.tabProperties.tabId or "",
            "title": tab.tabProperties.title or "",
            "index": tab.tabProperties.index or 0,
            "nestingLevel": nesting_level,
            "approximateCharacterCount": char_count,
            "approximateWordCount": word_count,
        }

        if tab.tabProperties.parentTabId:
            tab_meta_dict["parentTabId"] = tab.tabProperties.parentTabId

        if tab.childTabs and current_depth < max_depth - 1:
            tab_meta_dict["childTabs"] = build_tab_metadata_recursive(
                tab.childTabs, max_depth, current_depth + 1
            )

        result.append(tab_meta_dict)

    return result


def count_tab_chars_recursive(tab_meta: dict) -> int:
    """Recursively count characters in a tab and its children.

    Args:
        tab_meta: TabMetadata dict potentially with childTabs

    Returns:
        Total character count including all descendants
    """
    count: int = tab_meta.get("approximateCharacterCount", 0)
    if "childTabs" in tab_meta:
        count += sum(count_tab_chars_recursive(child) for child in tab_meta["childTabs"])
    return count


def count_tab_words_recursive(tab_meta: dict) -> int:
    """Recursively count words in a tab and its children.

    Args:
        tab_meta: TabMetadata dict potentially with childTabs

    Returns:
        Total word count including all descendants
    """
    count: int = tab_meta.get("approximateWordCount", 0)
    if "childTabs" in tab_meta:
        count += sum(count_tab_words_recursive(child) for child in tab_meta["childTabs"])
    return count


def _calculate_character_count(content: list[StructuralElement] | None) -> int:
    """Calculate total character count from body content.

    Args:
        content: List of structural elements from a body

    Returns:
        Total number of characters in the content
    """
    if not content:
        return 0

    char_count = 0
    for element in content:
        if element.paragraph:
            for el in element.paragraph.elements or []:
                if el.textRun and el.textRun.content:
                    char_count += len(el.textRun.content)
        elif element.table:
            for row in element.table.tableRows or []:
                for cell in row.tableCells or []:
                    char_count += _calculate_character_count(cell.content)

    return char_count


def _calculate_word_count(content: list[StructuralElement] | None) -> int:
    """Calculate total word count from body content.

    Args:
        content: List of structural elements from a body

    Returns:
        Total number of words in the content
    """
    if not content:
        return 0

    word_count = 0
    for element in content:
        if element.paragraph:
            for el in element.paragraph.elements or []:
                if el.textRun and el.textRun.content:
                    text = el.textRun.content.strip()
                    if text:
                        word_count += len(text.split())
        elif element.table:
            for row in element.table.tableRows or []:
                for cell in row.tableCells or []:
                    word_count += _calculate_word_count(cell.content)

    return word_count


def calculate_total_tabs_characters(tabs: list, max_depth: int = 4, current_depth: int = 0) -> int:
    """Calculate total character count from all tabs recursively.

    Args:
        tabs: List of Tab objects
        max_depth: Maximum recursion depth (Google Docs enforces 3 levels, using 4 for safety)
        current_depth: Current recursion depth

    Returns:
        Total character count across all tabs
    """
    if current_depth >= max_depth:
        return 0

    total = 0
    for tab in tabs:
        if tab.documentTab and tab.documentTab.body:
            total += _calculate_character_count(tab.documentTab.body.content)
        if tab.childTabs:
            total += calculate_total_tabs_characters(tab.childTabs, max_depth, current_depth + 1)
    return total


def calculate_total_tabs_words(tabs: list, max_depth: int = 4, current_depth: int = 0) -> int:
    """Calculate total word count from all tabs recursively.

    Args:
        tabs: List of Tab objects
        max_depth: Maximum recursion depth (Google Docs enforces 3 levels, using 4 for safety)
        current_depth: Current recursion depth

    Returns:
        Total word count across all tabs
    """
    if current_depth >= max_depth:
        return 0

    total = 0
    for tab in tabs:
        if tab.documentTab and tab.documentTab.body:
            total += _calculate_word_count(tab.documentTab.body.content)
        if tab.childTabs:
            total += calculate_total_tabs_words(tab.childTabs, max_depth, current_depth + 1)
    return total


def build_document_content_result(document: Any, doc_dict: dict, return_format: Any) -> dict:
    """Build a DocumentContentResult from a document.

    Args:
        document: Parsed Document object
        doc_dict: Raw document dict for conversion functions
        return_format: Desired output format (DocumentFormat enum)

    Returns:
        DocumentContentResult with content and metadata
    """
    tabs_count = len(document.tabs) if document.tabs else 0

    total_char_count = 0
    total_word_count = 0
    main_body_char_count = 0
    main_body_word_count = 0

    if document.tabs and len(document.tabs) > 0:
        total_char_count = calculate_total_tabs_characters(document.tabs)
        total_word_count = calculate_total_tabs_words(document.tabs)

    if document.body:
        main_body_char_count = _calculate_character_count(document.body.content)
        main_body_word_count = _calculate_word_count(document.body.content)
        if tabs_count == 0:
            total_char_count = main_body_char_count
            total_word_count = main_body_word_count

    content: str
    if return_format == DocumentFormat.DOCMD:
        content = build_docmd(document).to_string()
    elif return_format == DocumentFormat.MARKDOWN:
        content = convert_document_to_markdown(doc_dict, include_all_tabs=True)
    else:
        content = convert_document_to_html(doc_dict, include_all_tabs=True)

    return {
        "documentId": document.documentId or "",
        "title": document.title or "",
        "documentUrl": f"https://docs.google.com/document/d/{document.documentId}/edit",
        "content": content,
        "format": return_format.value,
        "tabs_count": tabs_count,
        "total_character_count": total_char_count,
        "total_word_count": total_word_count,
        "main_body_character_count": main_body_char_count,
        "main_body_word_count": main_body_word_count,
    }


def build_search_retrieve_response(documents: list[dict], search_response: dict) -> dict:
    """Build final response for search and retrieve operation.

    Args:
        documents: List of processed documents with content
        search_response: Response from search_documents

    Returns:
        Complete search and retrieve response
    """
    result_dict: dict = {
        "documents_count": len(documents),
        "documents": documents,
        "has_more": search_response["has_more"],
    }

    if "pagination_token" in search_response:
        result_dict["pagination_token"] = search_response["pagination_token"]

    return result_dict
