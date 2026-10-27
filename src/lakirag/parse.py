"""Parse Finlex Akoma Ntoso XML into passages, one per section."""

import re
import xml.etree.ElementTree as ET

AKN = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"
VERSION_SUFFIX = re.compile(r"v\d{8}")
REPEALED = "on kumottu L:lla"


def is_new(elem: ET.Element, seen: set[str]) -> bool:
    """Return False if an element with the same eId (ignoring version tags) came earlier.
    Finlex puts the newest wording first, so a repeated eId is an older version"""

    eid = elem.get("eId")
    if eid is None:
        return True
    base = VERSION_SUFFIX.sub("", eid)
    if base in seen:
        return False
    seen.add(base)
    return True


def clean_text(elem: ET.Element, seen: set[str]) -> str:
    """Return the text of elem without editorial notes, older versions or repealed parts."""
    if elem.tag == f"{AKN}hcontainer" or not is_new(elem, seen):
        return ""
    parts = [elem.text or ""]
    for child in elem:
        parts.append(clean_text(child, seen))
        parts.append(child.tail or "")
    text = " ".join("".join(parts).split())
    if elem.get("eId") and REPEALED in text:
        return ""
    return text
