# berita_analysis.py
from __future__ import annotations

import re
import time
from typing import Iterable, List, Dict, Tuple
import pandas as pd
import feedparser

# ==========================
# Konfigurasi & Utilities
# ==========================
DEFAULT_SOURCES: List[str] = [
    "https://finance.detik.com/rss",
    "https://www.cnbcindonesia.com/market/rss",
    "https://investasi.kontan.co.id/rss",
    "https://market.bisnis.com/rss",
    "https://money.kompas.com/rss",
    "https://www.idnfinancials.com/id/rss",
]

def get_source_labels() -> Dict[str, str]:
    """Label -> URL agar bisa dipakai di sidebar multiselect."""
    return {
        "Detik Finance": "https://finance.detik.com/rss",
        "CNBC Indonesia": "https://www.cnbcindonesia.com/market/rss",
        "Kontan": "https://investasi.kontan.co.id/rss",
        "Bisnis Market": "https://market.bisnis.com/rss",
        "Kompas Money": "https://money.kompas.com/rss",
        "IDN Financials": "https://www.idnfinancials.com/id/rss",
    }

def load_alias(path: str = "data/kode_saham/kode_saham.csv") -> Dict[str, str]:
    """
    Baca mapping kode -> nama perusahaan (tanpa 'Tbk.').
    CSV diharapkan punya kolom: Kode, Nama Perusahaan
    """
    try:
        df = pd.read_csv(path)
        return {
            str(row["Kode"]).strip(): str(row["Nama Perusahaan"]).replace("Tbk.", "").strip()
            for _, row in df.iterrows()
            if pd.notna(row.get("Kode"))
        }
    except Exception as e:
        print(f"⚠️ Gagal load alias: {e}")
        return {}

def _normalize_aliases(kode: str, nama: str | None) -> List[str]:
    """
    Perkaya keyword pencarian: KODE, nama lengkap, token penting.
    Contoh: 'Bank Central Asia' -> ['Bank Central Asia','Bank','Central','Asia'] (panjang>2 huruf).
    """
    kws = {kode}
    if nama:
        clean = re.sub(r"\bTbk\.?\b", "", nama, flags=re.I).strip()
        kws.add(clean)
        # tokenisasi ringan
        tokens = [t for t in re.split(r"[^\w]+", clean) if len(t) > 2]
        kws.update(tokens)
    return sorted(kws, key=str.lower)

def _match(blob: str, keywords: Iterable[str]) -> bool:
    text = (blob or "").lower()
    for kw in keywords:
        if not kw:
            continue
        pat = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pat, text):
            return True
    return False

def _parse_feeds(sources: Iterable[str], retries: int = 1, sleep: float = 0.6):
    """
    Ambil item dari banyak RSS dengan retry ringan.
    Return list of dicts: judul, link, summary, pubDate, source
    """
    items = []
    for url in sources:
        feed = None
        for _ in range(retries + 1):
            try:
                feed = feedparser.parse(url)
                if getattr(feed, "entries", None):
                    break
            except Exception:
                pass
            time.sleep(sleep)

        if not feed or not getattr(feed, "entries", None):
            continue

        src_title = (getattr(feed, "feed", {}) or {}).get("title", url)
        for e in feed.entries:
            items.append({
                "judul": (e.get("title") or "").strip(),
                "link": (e.get("link") or "").strip(),
                "summary": ((e.get("summary") or e.get("description") or "")).strip(),
                "pubDate": e.get("published", e.get("updated", "")),
                "source": src_title,
            })
    return items

# ==========================
# API Utama
# ==========================
def ambil_berita_dengan_alias(
    kode: str,
    alias_map: Dict[str, str],
    sources: Iterable[str] | None = None,
    extra_keywords: Iterable[str] | None = None,
) -> Tuple[str, List[dict]]:
    """
    Ambil berita dari RSS dan filter berdasarkan kode/alias.
    - kode: 'BBCA'
    - alias_map[kode] -> 'Bank Central Asia'
    """
    sources = list(sources) if sources else DEFAULT_SOURCES
    nama = alias_map.get(kode)
    aliases = _normalize_aliases(kode, nama)
    if extra_keywords:
        for k in extra_keywords:
            k = (k or "").strip()
            if k:
                aliases.append(k)
    # buang duplikat
    aliases = sorted(set(aliases), key=str.lower)

    # parse feeds
    items = _parse_feeds(sources)

    # filter berdasarkan kecocokan judul+ringkasan
    filtered = []
    for it in items:
        blob = f"{it.get('judul','')} {it.get('summary','')}"
        if _match(blob, aliases):
            filtered.append(it)

    # de-dupe by (title, link) + sort terbaru
    seen, uniq = set(), []
    for it in filtered:
        key = (it.get("judul"), it.get("link"))
        if key not in seen:
            uniq.append(it); seen.add(key)
    uniq.sort(key=lambda x: x.get("pubDate", ""), reverse=True)

    keyword_cari = ", ".join(aliases)
    return keyword_cari, uniq

__all__ = [
    "DEFAULT_SOURCES",
    "get_source_labels",
    "load_alias",
    "ambil_berita_dengan_alias",
]
