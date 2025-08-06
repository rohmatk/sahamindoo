import requests
from bs4 import BeautifulSoup

# Coba import Document dari readability-lxml
try:
    from readability import Document
except ImportError:
    Document = None
    print("⚠️ Modul `readability-lxml` tidak ditemukan. Fungsi ambil_isi_berita tidak akan bekerja sepenuhnya.")

def ambil_berita_google(keyword):
    """
    Scrape berita dari Google News RSS dengan kata kunci yang diberikan.
    """
    url = f"https://news.google.com/rss/search?q={keyword}+saham"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, features="xml")
    items = soup.findAll("item")
    berita = []
    for item in items[:10]:
        berita.append({
            'judul': item.title.text,
            'link': item.link.text,
            'pubDate': item.pubDate.text
        })
    return berita

def ambil_isi_berita(url):
    """
    Ambil isi berita utama dari sebuah URL dengan bantuan readability (jika tersedia).
    """
    if Document is None:
        return "⚠️ Modul `readability-lxml` belum terinstal."

    try:
        response = requests.get(url, timeout=10)
        doc = Document(response.text)
        html = doc.summary()
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except Exception as e:
        return f"❌ Gagal mengambil isi berita: {e}"
