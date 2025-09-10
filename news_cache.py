# news_cache.py
from db import get_engine  # ← tambahkan ini
import pandas as pd
import hashlib
from sqlalchemy.dialects.mysql import insert


UPSERT_SQL = """
INSERT INTO sahamiawa
(kode, judul, link, link_hash, summary, content, source, pub_date, cached_at, keywords)
VALUES
(:kode,:judul,:link,:link_hash,:summary,:content,:source,:pub_date,:cached_at,:keywords)
ON DUPLICATE KEY UPDATE
  judul=VALUES(judul),
  summary=VALUES(summary),
  content=VALUES(content),
  source=VALUES(source),
  pub_date=COALESCE(VALUES(pub_date), pub_date),
  cached_at=VALUES(cached_at),
  keywords=VALUES(keywords);
"""

def _sha256(s:str)->str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _norm_dt(s):
    if not s: return None
    try:
        return dtparser.parse(s)
    except Exception:
        return None

def save_articles(kode:str, keyword_cari:str, items:list[dict]):
    now = dt.datetime.utcnow()
    rows = []
    for it in items:
        rows.append({
            "kode": kode,
            "judul": it.get("judul","")[:10240],
            "link": it.get("link",""),
            "link_hash": _sha256(it.get("link","")),
            "summary": it.get("summary",""),
            "content": it.get("content",""),   # bisa kosong; isi setelah readability
            "source": it.get("source",""),
            "pub_date": _norm_dt(it.get("pubDate")),
            "cached_at": now,
            "keywords": keyword_cari,
        })
    return exec_many(UPSERT_SQL, rows)

def load_cached(kode:str, max_age_hours:int=12):
    q = """
    SELECT id,kode,judul,link,summary,content,source,pub_date,cached_at,keywords
    FROM sahamiawa
    WHERE kode = :kode
    ORDER BY COALESCE(pub_date, cached_at) DESC
    """
    df = fetch_df(q, kode=kode)
    if df.empty:
        return False, df
    latest = df["cached_at"].max()
    age = (dt.datetime.utcnow() - latest.replace(tzinfo=None)).total_seconds()/3600
    return age <= max_age_hours, df

def query_cached(kode:str, limit:int=30):
    q = """
    SELECT id, judul, link, source, pub_date, summary, content
    FROM sahamiawa
    WHERE kode=:kode
    ORDER BY COALESCE(pub_date, cached_at) DESC
    LIMIT :lim
    """
    return fetch_df(q, kode=kode, lim=limit)

def upsert_news(kode, news_list):
    """
    Simpan atau update berita hasil scraping ke tabel sahamiwa.
    """
    if not news_list:
        return

    df = pd.DataFrame(news_list)
    df["kode"] = kode
    df["link_hash"] = df["link"].apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
    df["cached_at"] = pd.Timestamp.utcnow()

    engine = get_engine()
    with engine.begin() as conn:
        for _, row in df.iterrows():
            stmt = insert(st.table("sahamiwa")).values(**row.to_dict())
            stmt = stmt.on_duplicate_key_update(
                summary=stmt.inserted.summary,
                content=stmt.inserted.content,
                pub_date=stmt.inserted.pub_date,
                cached_at=stmt.inserted.cached_at,
                keywords=stmt.inserted.keywords
            )
            conn.execute(stmt)

def load_cached(kode, max_age_hours=24):
    q = f"""
    SELECT * FROM sahamiwa
    WHERE kode = %s
      AND cached_at >= NOW() - INTERVAL {max_age_hours} HOUR
    ORDER BY pub_date DESC
    """
    with get_engine().begin() as conn:
        df = pd.read_sql(q, conn, params=[kode])
    return not df.empty, df
