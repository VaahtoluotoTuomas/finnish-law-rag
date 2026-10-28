import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from lakirag import parse
from lakirag.cli import main

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

SECTION_WITH_VERSIONS = f"""
<section xmlns="{parse.AKN[1:-1]}" eId="chp_7__sec_2v20100746">
  <num>2 §</num>
  <heading eId="chp_7__sec_2__headingv20100746">Otsikko</heading>
  <subsection eId="chp_7__sec_2__subsec_1v20260031">
    <content><p><i>1 momentti on kumottu L:lla <ref>16.1.2026/31</ref>.</i></p></content>
  </subsection>
  <subsection eId="chp_7__sec_2__subsec_1v20100746">
    <content><p>Vanha ensimmäinen momentti.</p></content>
  </subsection>
  <subsection eId="chp_7__sec_2__subsec_2v20260031">
    <content><p>Uusi toinen momentti, katso <ref>9 §</ref> tarkemmin.</p></content>
  </subsection>
  <hcontainer name="noteAuthorial"><content><p>Aiempi sanamuoto kuuluu:</p></content></hcontainer>
  <subsection eId="chp_7__sec_2__subsec_2v20100746">
    <content><p>Vanha toinen momentti.</p></content>
  </subsection>
</section>
"""


@pytest.fixture(scope="module")
def passages():
    return [p for name in parse.ABBREVIATIONS for p in parse.parse_law(RAW_DIR / f"{name}.xml")]


def test_compact():
    assert parse.compact("6 a luku") == "6a"
    assert parse.compact("14 a §") == "14a"


def test_parse_section_keeps_newest_wording_and_drops_notes():
    section = ET.fromstring(SECTION_WITH_VERSIONS)
    [passage] = parse.parse_section(section, set(), {"id": "KSL 7:2"})

    assert passage["id"] == "KSL 7:2"
    assert passage["title"] == "Otsikko"
    assert passage["text"] == "Otsikko. Uusi toinen momentti, katso 9 § tarkemmin."


def test_parse_section_skips_repealed_section():
    section = ET.fromstring(
        f'<section xmlns="{parse.AKN[1:-1]}" eId="chp_1__sec_6v19940016"><num>6 §</num>'
        "<content><p>6 § on kumottu L:lla 5.1.1994/16.</p></content></section>"
    )
    assert parse.parse_section(section, set(), {"id": "KSL 1:6"}) == []


def test_ids_are_unique(passages):
    ids = [p["id"] for p in passages]
    assert len(ids) == len(set(ids))


def test_texts_are_not_empty_or_repealed(passages):
    assert all(p["text"].strip() for p in passages)
    assert not any(parse.REPEALED in p["text"] for p in passages)


def test_both_laws_have_passages(passages):
    laws = {p["law"] for p in passages}
    assert laws == {"Kuluttajansuojalaki", "Vakuutussopimuslaki"}


def test_passage_count_is_reasonable(passages):
    assert 400 < len(passages) < 600


def test_long_sections_are_split(passages):
    ids = {p["id"] for p in passages}
    assert "KSL 6:9" not in ids
    assert {"KSL 6:9 #1", "KSL 6:9 #2"} <= ids


def test_known_section(passages):
    by_id = {p["id"]: p for p in passages}
    withdrawal = by_id["KSL 6:14"]
    assert withdrawal["title"] == "Peruuttamisoikeus"
    assert withdrawal["chapter"] == "6 luku Kotimyynti ja etämyynti"
    assert withdrawal["url"] == "https://www.finlex.fi/fi/lainsaadanto/1978/38#chp_6__sec_14"
    assert "VSL 22" in by_id


def test_cli_build(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("lakirag.cli.RAW_DIR", RAW_DIR)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    assert main(["build"]) == 0
    lines = (tmp_path / "data" / "passages.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["id"] == "KSL 1:1"
    assert f"{len(lines)} passages" in capsys.readouterr().out
