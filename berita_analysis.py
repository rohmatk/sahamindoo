import pandas as pd
from scraping import ambil_berita_google

def load_alias(path="data/kode_saham/kode_saham.csv"):
    try:
        df_alias = pd.read_csv(path)
        saham_alias = {
            row['Kode']: str(row['Nama Perusahaan']).replace("Tbk.", "").strip()
            for _, row in df_alias.iterrows()
        }
        return saham_alias
    except Exception:
        return {}

def ambil_berita_dengan_alias(kode_saham, alias_dict):
    nama_alias = alias_dict.get(kode_saham, "")
    keyword_cari = f"{kode_saham} {nama_alias}".strip()
    berita = ambil_berita_google(keyword_cari)
    return keyword_cari, berita

