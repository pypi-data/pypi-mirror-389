"""
Google Docs to HTML converter.
"""

import html as html_module


def convert_document_to_html(document: dict, include_all_tabs: bool = True) -> str:
    """Convert a Google Docs document to HTML format.

    Args:
        document: Document dict from Google Docs API
        include_all_tabs: Whether to include all tabs (True) or just main body (False)

    Returns:
        HTML string representation of the document
    """
    escaped_title = html_module.escape(document.get("title", ""))
    html = (
        "<html><head>"
        f"<title>{escaped_title}</title>"
        f'<meta name="documentId" content="{document["documentId"]}">'
        "</head><body>"
    )

    if include_all_tabs and "tabs" in document and document["tabs"]:
        html += _convert_tabs_to_html(document["tabs"])
    else:
        html += _convert_body_to_html(document.get("body", {}))

    html += "</body></html>"
    return html


def convert_structural_element(element: dict, wrap_paragraphs: bool = True) -> str:
    """Convert a structural element to HTML.

    Args:
        element: Structural element dict
        wrap_paragraphs: Whether to wrap paragraphs in <p> tags

    Returns:
        HTML string
    """
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        paragraph_content = ""

        prepend, append = get_paragraph_style_tags(
            style=element["paragraph"]["paragraphStyle"],
            wrap_paragraphs=wrap_paragraphs,
        )

        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            paragraph_content += extract_paragraph_content(item["textRun"])

        if not paragraph_content:
            return ""

        return f"{prepend}{paragraph_content.strip()}{append}"

    elif "table" in element:
        table = [
            [
                "".join([
                    convert_structural_element(element=cell_element, wrap_paragraphs=False)
                    for cell_element in cell["content"]
                ])
                for cell in row["tableCells"]
            ]
            for row in element["table"]["tableRows"]
        ]
        return table_list_to_html(table)

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def extract_paragraph_content(text_run: dict) -> str:
    """Extract content from a paragraph text run.

    Args:
        text_run: Text run dict

    Returns:
        Styled HTML string
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
        Styled content with HTML tags
    """
    content = content.replace("\u000b", "\n")  # Replace vertical tab with newline
    content = content.rstrip("\n")
    content = content.replace("\n", "<br>")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"<i>{content}</i>"
    if bold:
        content = f"<b>{content}</b>"
    return content


def get_paragraph_style_tags(style: dict, wrap_paragraphs: bool = True) -> tuple[str, str]:
    """Get HTML opening and closing tags for paragraph style.

    Args:
        style: Paragraph style dict
        wrap_paragraphs: Whether to wrap in paragraph tags

    Returns:
        Tuple of (opening_tag, closing_tag)
    """
    named_style = style["namedStyleType"]
    if named_style == "NORMAL_TEXT":
        return ("<p>", "</p>") if wrap_paragraphs else ("", "")
    elif named_style == "TITLE":
        return "<h1>", "</h1>"
    elif named_style == "SUBTITLE":
        return "<h2>", "</h2>"
    elif named_style.startswith("HEADING_"):
        try:
            heading_level = int(named_style.split("_")[1])
        except ValueError:
            return ("<p>", "</p>") if wrap_paragraphs else ("", "")
        else:
            return f"<h{heading_level}>", f"</h{heading_level}>"
    return ("<p>", "</p>") if wrap_paragraphs else ("", "")


def table_list_to_html(table: list[list[str]]) -> str:
    """Convert a table list to HTML.

    Args:
        table: List of rows, where each row is a list of cell contents

    Returns:
        HTML table string
    """
    html = "<table>"
    for row in table:
        html += "<tr>"
        for cell in row:
            if cell.endswith("<br>"):
                cell = cell[:-4]
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    return html


def _flatten_tabs_for_html(
    tabs: list[dict], max_depth: int = 4, current_depth: int = 0
) -> list[dict]:
    """Flatten tab hierarchy using depth-first traversal for HTML conversion.

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
            result.extend(_flatten_tabs_for_html(tab["childTabs"], max_depth, current_depth + 1))
    return result


def _convert_tabs_to_html(tabs: list[dict]) -> str:
    """Convert all tabs to HTML format.

    Args:
        tabs: List of tab dicts

    Returns:
        HTML string for all tabs
    """
    html = ""
    flattened_tabs = _flatten_tabs_for_html(tabs)

    for tab in flattened_tabs:
        html += _convert_single_tab_to_html(tab)

    return html


def _convert_single_tab_to_html(tab: dict) -> str:
    """Convert a single tab to HTML.

    Args:
        tab: Single tab dict

    Returns:
        HTML string for the tab
    """
    if "documentTab" not in tab or "tabProperties" not in tab:
        return ""

    tab_props = tab.get("tabProperties")
    if not tab_props:
        return ""

    nesting_level = _validate_nesting_level_for_html(tab_props.get("nestingLevel", 0))
    tab_title = tab_props.get("title", "Untitled")
    tab_id = tab_props.get("tabId", "")

    escaped_tab_id = html_module.escape(tab_id, quote=True)
    escaped_tab_title = html_module.escape(tab_title, quote=True)

    header_level = min(nesting_level + 1, 6)
    html = (
        f'<section id="tab-{escaped_tab_id}" data-title="{escaped_tab_title}" '
        f'data-level="{nesting_level}">'
        f"<h{header_level}>{html_module.escape(tab_title)}</h{header_level}>"
    )

    html += _convert_tab_body_to_html(tab.get("documentTab", {}))
    html += "</section>"

    return html


def _convert_body_to_html(body: dict) -> str:
    """Convert document body to HTML.

    Args:
        body: Body dict with content

    Returns:
        HTML string
    """
    html = ""
    for element in body.get("content", []):
        html += convert_structural_element(element)
    return html


def _convert_tab_body_to_html(doc_tab: dict) -> str:
    """Convert tab body content to HTML.

    Args:
        doc_tab: DocumentTab dict

    Returns:
        HTML string
    """
    body = doc_tab.get("body")
    if not body:
        return ""

    html = ""
    for element in body.get("content", []):
        html += convert_structural_element(element)
    return html


def _validate_nesting_level_for_html(nesting_level: int) -> int:
    """Validate and clamp nesting level to safe range.

    Args:
        nesting_level: The nesting level to validate

    Returns:
        Validated nesting level (0-5)
    """
    if not isinstance(nesting_level, int) or nesting_level < 0:
        return 0
    return nesting_level
