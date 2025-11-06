"""
Google Docs to Markdown converter.

File organization:
1. Public functions (convert_document_to_markdown, convert_structural_element, etc.)
2. Private helper functions (prefixed with _) at the end
"""

import arcade_google_docs.doc_to_html as doc_to_html


def convert_document_to_markdown(document: dict, include_all_tabs: bool = True) -> str:
    """Convert a Google Docs document to Markdown format.

    Args:
        document: Document dict from Google Docs API
        include_all_tabs: Whether to include all tabs (True) or just main body (False)

    Returns:
        Markdown string representation of the document
    """
    md = f"---\ntitle: {document['title']}\ndocumentId: {document['documentId']}\n---\n"

    if include_all_tabs and "tabs" in document and document["tabs"]:
        md += _convert_tabs_to_markdown(document["tabs"])
    else:
        md += _convert_body_to_markdown(document.get("body", {}))

    return md


def convert_structural_element(element: dict) -> str:
    """Convert a structural element to markdown.

    Args:
        element: Structural element dict

    Returns:
        Markdown string
    """
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        md = ""
        prepend = get_paragraph_style_prepend_str(element["paragraph"]["paragraphStyle"])
        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            content = extract_paragraph_content(item["textRun"])
            md += f"{prepend}{content}"
        return md

    elif "table" in element:
        return doc_to_html.convert_structural_element(element)

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def extract_paragraph_content(text_run: dict) -> str:
    """Extract and style paragraph content.

    Args:
        text_run: Text run dict

    Returns:
        Styled markdown string
    """
    content = text_run["content"]
    style = text_run["textStyle"]
    return apply_text_style(content, style)


def apply_text_style(content: str, style: dict) -> str:
    """Apply text styling to content.

    Args:
        content: Text content
        style: Style dict

    Returns:
        Styled content with markdown formatting
    """
    append = "\n" if content.endswith("\n") else ""
    content = content.rstrip("\n")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"_{content}_"
    if bold:
        content = f"**{content}**"
    return f"{content}{append}"


def get_paragraph_style_prepend_str(style: dict) -> str:
    """Get markdown prefix for paragraph style.

    Args:
        style: Paragraph style dict

    Returns:
        Markdown prefix string (e.g., "# ", "## ", etc.)
    """
    named_style = style["namedStyleType"]
    if named_style == "NORMAL_TEXT":
        return ""
    elif named_style == "TITLE":
        return "# "
    elif named_style == "SUBTITLE":
        return "## "
    elif named_style.startswith("HEADING_"):
        try:
            heading_level = int(named_style.split("_")[1])
            return f"{'#' * heading_level} "
        except ValueError:
            return ""
    return ""


def _flatten_tabs_for_conversion(
    tabs: list[dict], max_depth: int = 4, current_depth: int = 0
) -> list[dict]:
    """Flatten tab hierarchy using depth-first traversal for conversion.

    Args:
        tabs: List of tab dicts with potential childTabs
        max_depth: Maximum recursion depth (Google Docs enforces 3 levels, using 4 for safety)
        current_depth: Current recursion depth

    Returns:
        Flattened list in depth-first order
    """
    if current_depth >= max_depth:
        return []

    result: list[dict] = []
    for tab in tabs:
        result.append(tab)
        if tab.get("childTabs"):
            result.extend(
                _flatten_tabs_for_conversion(tab["childTabs"], max_depth, current_depth + 1)
            )
    return result


def _convert_tabs_to_markdown(tabs: list[dict]) -> str:
    """Convert all tabs to markdown format.

    Args:
        tabs: List of tab dicts

    Returns:
        Markdown string for all tabs
    """
    md = ""
    flattened_tabs = _flatten_tabs_for_conversion(tabs)

    for tab in flattened_tabs:
        md += _convert_single_tab_to_markdown(tab)

    return md


def _convert_single_tab_to_markdown(tab: dict) -> str:
    """Convert a single tab to markdown.

    Args:
        tab: Single tab dict

    Returns:
        Markdown string for the tab
    """
    if "documentTab" not in tab or "tabProperties" not in tab:
        return ""

    tab_props = tab.get("tabProperties")
    if not tab_props:
        return ""

    nesting_level = _validate_nesting_level(tab_props.get("nestingLevel", 0))
    tab_title = tab_props.get("title", "Untitled")
    tab_id = tab_props.get("tabId", "")

    header_prefix = "#" * (nesting_level + 1)
    md = f"\n{header_prefix} {tab_title}\n\n"
    if tab_id:
        md += f"<!-- Tab ID: {tab_id} -->\n\n"
    else:
        md += "<!-- Tab ID:  -->\n\n"

    md += _convert_tab_body_to_markdown(tab.get("documentTab", {}))

    return md


def _convert_body_to_markdown(body: dict) -> str:
    """Convert document body to markdown.

    Args:
        body: Body dict with content

    Returns:
        Markdown string
    """
    md = ""
    for element in body.get("content", []):
        md += convert_structural_element(element)
    return md


def _convert_tab_body_to_markdown(doc_tab: dict) -> str:
    """Convert tab body content to markdown.

    Args:
        doc_tab: DocumentTab dict

    Returns:
        Markdown string
    """
    body = doc_tab.get("body")
    if not body:
        return ""

    md = ""
    for element in body.get("content", []):
        md += convert_structural_element(element)
    return md


def _validate_nesting_level(nesting_level: int) -> int:
    """Validate and clamp nesting level to safe range.

    Args:
        nesting_level: The nesting level to validate

    Returns:
        Validated nesting level (0-5)
    """
    if not isinstance(nesting_level, int) or nesting_level < 0:
        return 0
    return min(nesting_level, 5)
