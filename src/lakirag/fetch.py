"""Download consolidated Finnish statutes from the Finlex open data API."""

import io
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://opendata.finlex.fi/finlex/avoindata/v1/akn/fi/act/statute-consolidated"
USER_AGENT = "finnish-law-rag/0.1 (+https://github.com/VaahtoluotoTuomas/finnish-law-rag)"

# Pinned versions keep the passages and the evaluation reproducible
# The tag after "fin@" is the year and number of the latest amending act.
LAWS = {
    "ksl": "1978/38/fin@20260835",
    "vsl": "1994/543/fin@20200324",
}


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read()


def extract_main_xml(akn_zip: bytes) -> bytes:
    """A main.akn file is a zip archive with the document in main.xml."""
    with zipfile.ZipFile(io.BytesIO(akn_zip)) as archive:
        return archive.read("main.xml")


def fetch_all(raw_dir: Path) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, version in LAWS.items():
        xml = extract_main_xml(download(f"{API_URL}/{version}/main.akn"))
        path = raw_dir / f"{name}.xml"
        path.write_bytes(xml)
        paths.append(path)
    return paths
