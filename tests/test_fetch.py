import io
import zipfile

from lakirag import fetch
from lakirag.cli import main


def make_akn_zip(xml: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("main.xml", xml)
    return buffer.getvalue()


def test_extract_main_xml():
    xml = "<akomaNtoso>pykälä</akomaNtoso>".encode()
    assert fetch.extract_main_xml(make_akn_zip(xml)) == xml


def test_fetch_all_writes_one_file_per_law(tmp_path, monkeypatch):
    urls = []

    def fake_download(url):
        urls.append(url)
        return make_akn_zip(b"<akomaNtoso/>")

    monkeypatch.setattr(fetch, "download", fake_download)
    paths = fetch.fetch_all(tmp_path / "raw")

    assert sorted(p.name for p in paths) == ["ksl.xml", "vsl.xml"]
    assert all(p.read_bytes() == b"<akomaNtoso/>" for p in paths)
    assert all(url.endswith("/main.akn") for url in urls)
    assert any("/1978/38/fin@" in url for url in urls)
    assert any("/1994/543/fin@" in url for url in urls)


def test_cli_fetch(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fetch, "download", lambda url: make_akn_zip(b"<akomaNtoso/>"))
    monkeypatch.chdir(tmp_path)

    assert main(["fetch"]) == 0
    assert (tmp_path / "data" / "raw" / "ksl.xml").exists()
    assert "ksl.xml" in capsys.readouterr().out
