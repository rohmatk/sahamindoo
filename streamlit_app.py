import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
from scraping import ambil_isi_berita, ambil_berita_google
from berita_analysis import load_alias, ambil_berita_dengan_alias, get_source_labels
from news_cache import load_cached, upsert_news


from data_analysis import proses_data_ksei
from scraping import ambil_isi_berita
from visualization import (
    plot_line_trend_summary,
    tampilkan_pie_terakhir,
    plot_bar_per_kategori_terakhir,
    plot_line_per_kategori,
    tampilkan_tabel_trend_kategori,
    tampilkan_pivot_excel
)

# === Load & proses data ===
df, investor_mapping, local_cols, foreign_cols = proses_data_ksei()
if df is None:
    st.warning("Tidak ada data saham ditemukan.")
    st.stop()

# Pastikan kolom Bulan jadi datetime
df["Bulan"] = pd.to_datetime(df["Bulan"], errors="coerce")

# === FILTER di SIDEBAR ===
st.sidebar.header("Filter Data")
selected_code = st.sidebar.selectbox("📌 Pilih Kode Saham", sorted(df['Code'].unique()))
jenis_pilih = st.sidebar.radio("Jenis Investor", ["Lokal", "Asing"], horizontal=True)
kategori_pilih = st.sidebar.selectbox("Kategori Investor", list(investor_mapping.values()))

# Filter sesuai kode saham
df_code = df[df['Code'] == selected_code].copy()

# === Ringkasan lokal vs asing ===
df_lokal = df_code.groupby('Bulan')[local_cols].sum().reset_index()
df_asing = df_code.groupby('Bulan')[foreign_cols].sum().reset_index()
df_lokal['Jenis'] = 'Lokal'
df_asing['Jenis'] = 'Asing'

df_lokal.columns = ['Bulan'] + list(investor_mapping.values()) + ['Jenis']
df_asing.columns = ['Bulan'] + list(investor_mapping.values()) + ['Jenis']

df_all_raw = pd.concat([df_lokal, df_asing])
df_melt = df_all_raw.melt(
    id_vars=['Bulan', 'Jenis'],
    var_name='Kategori Lengkap',
    value_name='Jumlah Saham'
)

# === Plot tren bulanan sesuai filter ===
df_filtered = df_melt[
    (df_melt["Jenis"] == jenis_pilih) &
    (df_melt["Kategori Lengkap"] == kategori_pilih)
].copy()

if not df_filtered.empty:
    fig = px.line(
        df_filtered.sort_values("Bulan"),
        x="Bulan", y="Jumlah Saham",
        markers=True,
        title=f"Tren Bulanan {kategori_pilih} – {jenis_pilih} ({selected_code})",
        labels={"Jumlah Saham": "Jumlah Saham", "Bulan": "Bulan"}
    )
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Tidak ada data untuk filter yang dipilih.")

# === Visualisasi tambahan ===
# Total summary lokal vs asing
df_code['Total Lokal'] = df_code[local_cols].sum(axis=1)
df_code['Total Asing'] = df_code[foreign_cols].sum(axis=1)
df_summary = df_code.groupby('Bulan')[['Total Lokal', 'Total Asing']].sum().reset_index()
df_summary['Total'] = df_summary['Total Lokal'] + df_summary['Total Asing']
plot_line_trend_summary(df_summary, selected_code)
tampilkan_pie_terakhir(df_summary, selected_code)

# Pie & bar chart bulan terakhir
latest_month = df_melt['Bulan'].max()
df_all_latest = df_melt[df_melt['Bulan'] == latest_month].copy()
df_all_latest['Total'] = df_all_latest.groupby('Jenis')['Jumlah Saham'].transform('sum')
df_all_latest['Persentase'] = (df_all_latest['Jumlah Saham'] / df_all_latest['Total']) * 100
plot_bar_per_kategori_terakhir(df_all_latest, selected_code, latest_month)

# Grafik tren semua kategori
df_plot = df_melt.copy()
df_plot['Label'] = df_plot['Jenis'] + ' - ' + df_plot['Kategori Lengkap']
df_plot_grouped = df_plot.groupby(['Bulan', 'Label'])['Jumlah Saham'].sum().reset_index()
plot_line_per_kategori(df_plot_grouped, selected_code)

# Tabel perubahan
df_trend = df_melt.copy()
df_trend['Δ Saham'] = df_trend.groupby(['Jenis', 'Kategori Lengkap'])['Jumlah Saham'].diff().fillna(0).astype(int)
df_trend['Total'] = df_trend.groupby(['Bulan', 'Jenis'])['Jumlah Saham'].transform('sum')
df_trend['Persentase'] = (df_trend['Jumlah Saham'] / df_trend['Total']) * 100
df_trend['Status'] = df_trend['Δ Saham'].apply(lambda x: '⬆️ Naik' if x > 0 else ('⬇️ Turun' if x < 0 else '⏸️ Stabil'))
df_trend_display = df_trend.copy()
df_trend_display['Jumlah Saham'] = df_trend_display['Jumlah Saham'].map('{:,.0f}'.format)
df_trend_display['Δ Saham'] = df_trend_display['Δ Saham'].map('{:,.0f}'.format)
df_trend_display['Persentase'] = df_trend_display['Persentase'].map('{:.2f}%'.format)
tampilkan_tabel_trend_kategori(df_trend_display)

# Pivot Excel
df_pivot_table = df_trend.copy()
df_pivot_table['Bulan Format'] = pd.to_datetime(df_pivot_table['Bulan'], errors='coerce').dt.strftime('%b %Y')
df_pivot_table['Δ Saham'] = df_pivot_table['Δ Saham'].astype(int)
df_pivot_table['Jumlah Saham'] = df_pivot_table['Jumlah Saham'].astype(int)
df_pivot_table['Persentase'] = df_pivot_table['Persentase'].map(lambda x: f"{x:.2f}%")
df_pivot_table = df_pivot_table[['Kategori Lengkap', 'Bulan Format', 'Δ Saham', 'Jumlah Saham', 'Persentase']]
tampilkan_pivot_excel(df_pivot_table, selected_code)


# asumsi: selected_code & saham_alias sudah ada di atas
# --- Pastikan df sudah ada & kolom Code tersedia ---
# df = ...  # <- data utama kamu
# --- ALIAS & SUMBER RSS ---
saham_alias = load_alias()  # kalau gagal, fungsi sudah return {}
label_to_url = get_source_labels()

chosen_sources = st.sidebar.multiselect(
    "Sumber RSS",
    options=list(label_to_url.keys()),
    default=list(label_to_url.keys()),
    key="rss_sources_sidebar"
)
extra_kw = st.sidebar.text_input("Kata kunci tambahan (opsional, pisahkan koma)", "", key="extra_kw_sidebar")
extra_kw_list = [x.strip() for x in extra_kw.split(",") if x.strip()]

# Ambil dari RSS dgn filter longgar
keyword_cari, berita = ambil_berita_dengan_alias(
    selected_code,
    saham_alias,
    sources=[label_to_url[l] for l in chosen_sources] if chosen_sources else None,
    extra_keywords=extra_kw_list
)

# Fallback: kalau tetap kosong, ambil dari Google News berdasarkan kode+alias
if not berita:
    alias_txt = saham_alias.get(selected_code, "")
    berita = ambil_berita_google(f"{selected_code} {alias_txt}".strip())

st.subheader(f"🗞️ Berita Terkait Saham `{selected_code}`")
st.caption(f"🔎 Pencarian: `{selected_code}, {saham_alias.get(selected_code,'')}` • Sumber: {', '.join(chosen_sources) or 'Default'}")

if not berita:
    st.info("Belum ada berita yang cocok. Coba ubah sumber RSS atau tambah kata kunci.")
else:
    for it in berita[:25]:
        title = it.get("judul") or "(tanpa judul)"
        link  = it.get("link") or ""
        pub   = it.get("pubDate","")
        src   = it.get("source","")
        st.markdown(f"**[{title}]({link})**  \n<small>{src} • {pub}</small>", unsafe_allow_html=True)
        with st.expander("Lihat isi"):
            teks = ambil_isi_berita(link)
            st.write(teks or ("> " + (it.get("summary") or "Ringkasan tidak tersedia.")))
        st.divider()

# --- Sidebar: pilih saham & sumber ---
kode_list = sorted(df["Code"].unique())
selected_code = st.sidebar.selectbox("📌 Pilih Kode Saham", kode_list, key="sb_kode")

label_to_url = get_source_labels()
chosen_sources = st.sidebar.multiselect("Pilih RSS", list(label_to_url.keys()), default=list(label_to_url.keys()), key="sb_rss")
extra_kw = st.sidebar.text_input("Tambah kata kunci (opsional, pisahkan koma)", "", key="sb_kw")
extra_kw_list = [x.strip() for x in extra_kw.split(",") if x.strip()]
max_age = st.sidebar.slider("Maks umur cache (jam)", 1, 48, 12, key="sb_cache_age")

# --- Alias + cek cache ---
saham_alias = load_alias()
fresh, df_cache = load_cached(selected_code, max_age_hours=max_age)

if not fresh:
    # scrape baru
    sources = [label_to_url[l] for l in chosen_sources]
    keyword_cari, items = ambil_berita_dengan_alias(
        selected_code, saham_alias, sources=sources, extra_keywords=extra_kw_list
    )
    # isi content (opsional) pakai readability bila ingin
    filled = []
    for it in items:
        c = ambil_isi_berita(it["link"]) or ""
        it["content"] = c
        filled.append(it)
    saved = save_articles(selected_code, keyword_cari, filled)
    st.toast(f"✅ Cache diperbarui: {saved} artikel", icon="✅")

# --- tampilkan dari DB ---
df_news = query_cached(selected_code, limit=30)

st.subheader(f"🗞️ Berita `{selected_code}`")
if df_news.empty:
    st.info("Belum ada berita untuk kode ini.")
else:
    for _, row in df_news.iterrows():
        title = row["judul"]
        link  = row["link"]
        src   = row.get("source") or ""
        ts    = row.get("pub_date")
        st.markdown(f"### [{title}]({link})")
        st.caption(f"🕒 {ts} · {src}")
        with st.expander("Lihat isi"):
            body = row["content"] or row["summary"] or "❌ Konten tidak tersedia."
            st.markdown(body)

if st.button("🔄 Refresh berita sekarang", use_container_width=True):
    fresh = False  # paksa refresh pada blok di atas

keyword_cari, berita = ambil_berita_dengan_alias(selected_code, saham_alias, ...)
upsert_news(selected_code, berita)
