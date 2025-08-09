# scraping.py
import re
import html
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# Coba import Document dari readability-lxml (opsional)
try:
    from readability import Document
except Exception:
    Document = None

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 12

def ambil_berita_google(keyword: str, limit: int = 10):
    """Ambil berita dari Google News RSS (fallback cepat)."""
    url = f"https://news.google.com/rss/search?q={quote_plus(keyword)}"
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(r.content, features="xml")
    items = soup.find_all("item")
    out = []
    for it in items[:limit]:
        out.append({
            "judul": it.title.text if it.title else "",
            "link": it.link.text if it.link else "",
            "pubDate": it.pubDate.text if it.pubDate else "",
            "source": "Google News",
            "summary": "",
        })
    return out

def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return html.unescape(s)

def _fallback_text_from_html(html_text: str) -> str | None:
    """Kalau readability nggak ada/mentok, ambil <article>, <p> dkk."""
    soup = BeautifulSoup(html_text, "html.parser")
    # prioritas node artikel
    for sel in ["article", ".article", ".post", ".read__content", ".detail__body", ".content"]:
        node = soup.select_one(sel)
        if node:
            txt = _strip_html(str(node))
            if len(txt) > 120:
                return txt
    # fallback: gabung <p>
    ps = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    txt = " ".join(ps).strip()
    return txt if len(txt) > 120 else None

def ambil_isi_berita(url: str) -> str | None:
    """Ambil isi utama artikel. Kembalikan None bila gagal (biar UI pake ringkasan)."""
    if not url:
        return None
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        if not r.ok or "text/html" not in (r.headers.get("Content-Type") or ""):
            return None

        # 1) readability kalau tersedia
        if Document is not None:
            try:
                doc = Document(r.text)
                summary_html = doc.summary()
                txt = _strip_html(summary_html)
                if len(txt) > 120:
                    return txt
            except Exception:
                pass

        # 2) fallback manual
        return _fallback_text_from_html(r.text)
    except Exception:
        return None
