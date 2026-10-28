"""Parse Finlex Akoma Ntoso XML into passages, one per section."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from lakirag.fetch import LAWS

AKN = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"
VERSION_SUFFIX = re.compile(r"v\d{8}")
REPEALED = "on kumottu L:lla"
MAX_WORDS = 350
FINLEX_URL = "https://www.finlex.fi/fi/lainsaadanto"

# Abbreviation for passage ids, and whether sections are numbered per chapter
# (KSL 6:14) or across the whole act (VSL 22).
ABBREVIATIONS = {"ksl": ("KSL", True), "vsl": ("VSL", False)}


def is_new(elem: ET.Element, seen: set[str]) -> bool:
    """Return False if an element with the same eId (ignoring version tags) came earlier.
    Finlex puts the newest wording first, so a repeated eId is an older version
    """

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


def compact(num: str) -> str:
    """'6 a luku' -> '6a', '14 a §' -> '14a'."""
    return num.replace("luku", "").replace("§", "").replace(" ", "")


def parse_section(section: ET.Element, seen: set[str], shared: dict) -> list[dict]:
    """Turn a section into passages. shared holds the fields that come from the act and chapter.

    A repealed section gives no passages and a long one gives one passage per subsection.
    """
    if not is_new(section, seen):
        return []
    heading = section.find(f"{AKN}heading")
    title = clean_text(heading, seen) if heading is not None else ""
    texts = [clean_text(sub, seen) for sub in section.findall(f"{AKN}subsection")]
    subsections = [text for text in texts if text]
    if not subsections:
        return []

    def passage(id_: str, text: str) -> dict:
        full_text = f"{title}. {text}" if title else text
        return {**shared, "id": id_, "title": title, "text": full_text}

    if len(" ".join(subsections).split()) <= MAX_WORDS:
        return [passage(shared["id"], " ".join(subsections))]
    return [passage(f"{shared['id']} #{i}", text) for i, text in enumerate(subsections, start=1)]


def parse_law(path: Path) -> list[dict]:
    abbrev, by_chapter = ABBREVIATIONS[path.stem]
    root = ET.parse(path).getroot()
    law = root.findtext(f".//{AKN}docTitle", default="")
    url = f"{FINLEX_URL}/{LAWS[path.stem].split('/fin@')[0]}"
    body = root.find(f".//{AKN}hcontainer[@name='statuteProvisionsWrapper']")
    if body is None:
        raise ValueError(f"No statute text in {path}")

    seen: set[str] = set()
    passages = []
    for chapter in body.findall(f"{AKN}chapter"):
        chapter_num = chapter.findtext(f"{AKN}num", default="")
        chapter_heading = chapter.findtext(f"{AKN}heading", default="")
        for section in chapter.findall(f"{AKN}section"):
            num = section.findtext(f"{AKN}num", default="")
            id_ = f"{abbrev} {compact(num)}"
            if by_chapter:
                id_ = f"{abbrev} {compact(chapter_num)}:{compact(num)}"
            shared = {
                "id": id_,
                "law": law,
                "chapter": " ".join(f"{chapter_num} {chapter_heading}".split()),
                "section": " ".join(num.split()),
                "url": f"{url}#{VERSION_SUFFIX.sub('', section.get('eId', ''))}",
            }
            passages.extend(parse_section(section, seen, shared))
    return passages


def build(raw_dir: Path, out_path: Path) -> int:
    passages = [p for name in ABBREVIATIONS for p in parse_law(raw_dir / f"{name}.xml")]
    with out_path.open("w", encoding="utf-8") as f:
        for p in passages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return len(passages)
