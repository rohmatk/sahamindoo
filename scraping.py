import requests
from bs4 import BeautifulSoup
from readability import Document

def ambil_berita_google(keyword):
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
    try:
        response = requests.get(url)
        doc = Document(response.text)
        html = doc.summary()
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except:
        return ""
