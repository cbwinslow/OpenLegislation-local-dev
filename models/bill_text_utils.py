import re
from typing import List
from bs4 import BeautifulSoup, NavigableString

# Regex patterns translated from Java
BILL_TEXT_PAGE_START_PATTERN = re.compile(
    r"^(\s+\w.\s\d+(--\w)?)?\s{10,}(\d+)(\s{10,}(\w.\s\d+(--\w)?)?(\d+-\d+-\d(--\w)?)?)?$"
)
MAX_LINES_RES_PAGE = 60

IN_SENATE = "IN SENATE"
IN_ASSEMBLY = "IN ASSEMBLY"
IN_BOTH = "SENATE - ASSEMBLY"

BILL_HEADER_PATTERN = re.compile(
    r"^(?P<startingNewlines>\s*)"
    r"[ ]{3,}STATE OF NEW YORK\n"
    r"(?P<divider>(?:[ \w.\-]*\n){0,8})"
    r"[ ]{3,}(?P<chamber>" + f"{IN_SENATE}|{IN_ASSEMBLY}|{IN_BOTH}" + r")"
    r"(?:(?P<prefiledWhiteSpace>\s+)\(Prefiled\))?",
    re.MULTILINE
)

RESOLUTION_HEADER_PATTERN = re.compile(
    r"^\s+(?P<chamber>Senate|Assembly) *Resolution *No *\. *(\d+)\s+"
    r"BY:[\w '.\\:()-]+\n"
    r"(?:\s+(?P<verb>[A-Z]{2,}ING))?",
    re.IGNORECASE | re.MULTILINE,
)

def format_html_extracted_bill_text(text: str) -> str:
    """Reformat plain bill text that has been extracted from html"""
    match = BILL_HEADER_PATTERN.search(text)
    if match:
        replacement_parts = [match.group("startingNewlines")]
        replacement_parts.append(" " * 16 + "S T A T E   O F   N E W   Y O R K\n")
        replacement_parts.append(match.group("divider"))

        chamber_text = match.group("chamber")
        if chamber_text == IN_SENATE:
            replacement_parts.append(" " * 37 + "I N  S E N A T E")
        elif chamber_text == IN_ASSEMBLY:
            replacement_parts.append(" " * 35 + "I N  A S S E M B L Y")
        elif chamber_text == IN_BOTH:
            replacement_parts.append(" " * 30 + "S E N A T E - A S S E M B L Y")

        if match.group("prefiledWhiteSpace"):
            replacement_parts.append(match.group("prefiledWhiteSpace") + "(PREFILED)")

        replacement = "".join(replacement_parts)
        text = BILL_HEADER_PATTERN.sub(replacement, text, count=1)

    return text

def _process_text_node(element, string_builder: List[str], inside_u_tag: bool):
    inside_u_tag = inside_u_tag or element.name == 'u'
    for node in element.children:
        if hasattr(node, 'name') and node.name: # It's a tag
            _process_text_node(node, string_builder, inside_u_tag)
        elif isinstance(node, NavigableString):
            text = str(node)
            if inside_u_tag:
                text = text.upper()
            string_builder.append(text)

def convert_html_to_plain_text(html_text: str) -> str:
    """Extracts plain bill text from html."""
    soup = BeautifulSoup(html_text, 'html.parser')
    pre_tags = soup.select('pre')
    if not pre_tags:
        return html_text

    text_builder = []
    for tag in pre_tags:
        _process_text_node(tag, text_builder, False)

    text = "".join(text_builder)
    # Remove some undesirable characters
    text = re.sub(r"[\r\uFEFF-\uFFFF]+", "", text)
    # Split into lines, strip each line, and join back.
    lines = [line.strip() for line in text.split('\n')]
    # Filter out empty lines that were just whitespace
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)