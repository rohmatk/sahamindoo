
import streamlit as st
import pandas as pd
import plotly.express as px

from data_analysis import proses_data_ksei
from berita_analysis import load_alias, ambil_berita_dengan_alias
from scraping import ambil_isi_berita
from visualization import (
    plot_bar_perbandingan,
    plot_line_trend_summary,
    tampilkan_pie_terakhir,
    plot_bar_per_kategori_terakhir,
    plot_line_per_kategori,
    tampilkan_tabel_trend_kategori,
    tampilkan_pivot_excel
)

# ✅ Ambil dan proses data saham
df, investor_mapping, local_cols, foreign_cols = proses_data_ksei()
if df is None:
    st.warning("Tidak ada data saham ditemukan.")
    st.stop()

# 📌 Pilih kode saham
selected_code = st.selectbox("📌 Pilih Kode Saham", sorted(df['Code'].unique()))
df_code = df[df['Code'] == selected_code].copy()

# 🧠 Alias perusahaan
saham_alias = load_alias()
keyword_cari, berita = ambil_berita_dengan_alias(selected_code, saham_alias)

# 📊 Ringkasan lokal vs asing bulanan
df_lokal = df_code.groupby('Bulan')[local_cols].sum().reset_index()
df_asing = df_code.groupby('Bulan')[foreign_cols].sum().reset_index()
df_lokal['Jenis'] = 'Lokal'
df_asing['Jenis'] = 'Asing'

df_lokal.columns = ['Bulan'] + list(investor_mapping.values()) + ['Jenis']
df_asing.columns = ['Bulan'] + list(investor_mapping.values()) + ['Jenis']

df_all_raw = pd.concat([df_lokal, df_asing])
df_melt = df_all_raw.melt(id_vars=['Bulan', 'Jenis'], var_name='Kategori Lengkap', value_name='Jumlah Saham')

def plot_bar_perbandingan(df_melt, selected_code):
    fig = px.bar(
        df_melt,
        x='Bulan',
        y='Jumlah Saham',
        color='Jenis',
        facet_col='Kategori Lengkap',
        facet_col_wrap=3,
        title=f"Perbandingan Kepemilikan per Bulan: Lokal vs Asing - {selected_code}",
        height=800
    )
    st.plotly_chart(fig, use_container_width=True, key=f"bar-{selected_code}")


# Ringkasan total
df_code['Total Lokal'] = df_code[local_cols].sum(axis=1)
df_code['Total Asing'] = df_code[foreign_cols].sum(axis=1)
df_summary = df_code.groupby('Bulan')[['Total Lokal', 'Total Asing']].sum().reset_index()
df_summary['Total'] = df_summary['Total Lokal'] + df_summary['Total Asing']

plot_line_trend_summary(df_summary, selected_code)
tampilkan_pie_terakhir(df_summary, selected_code)

# 📊 Bar chart per kategori
df_all = df_melt.copy()
latest_month = df_all['Bulan'].max()
df_all_latest = df_all[df_all['Bulan'] == latest_month].copy()
df_all_latest['Total'] = df_all_latest.groupby('Jenis')['Jumlah Saham'].transform('sum')
df_all_latest['Persentase'] = (df_all_latest['Jumlah Saham'] / df_all_latest['Total']) * 100

plot_bar_per_kategori_terakhir(df_all_latest, selected_code, latest_month)

# 📈 Grafik tren per kategori investor
df_plot = df_all.copy()
df_plot['Label'] = df_plot['Jenis'] + ' - ' + df_plot['Kategori Lengkap']
df_plot_grouped = df_plot.groupby(['Bulan', 'Label'])['Jumlah Saham'].sum().reset_index()
plot_line_per_kategori(df_plot_grouped, selected_code)

# 📊 Tabel perubahan per bulan
df_trend = df_all.copy()
df_trend['Δ Saham'] = df_trend.groupby(['Jenis', 'Kategori Lengkap'])['Jumlah Saham'].diff().fillna(0).astype(int)
df_trend['Total'] = df_trend.groupby(['Bulan', 'Jenis'])['Jumlah Saham'].transform('sum')
df_trend['Persentase'] = (df_trend['Jumlah Saham'] / df_trend['Total']) * 100
df_trend['Status'] = df_trend['Δ Saham'].apply(lambda x: '⬆️ Naik' if x > 0 else ('⬇️ Turun' if x < 0 else '⏸️ Stabil'))

df_trend_display = df_trend.copy()
df_trend_display['Jumlah Saham'] = df_trend_display['Jumlah Saham'].map('{:,.0f}'.format)
df_trend_display['Δ Saham'] = df_trend_display['Δ Saham'].map('{:,.0f}'.format)
df_trend_display['Persentase'] = df_trend_display['Persentase'].map('{:.2f}%'.format)
tampilkan_tabel_trend_kategori(df_trend_display)

# 📊 Pivot multi-kolom Excel
df_pivot_table = df_trend.copy()
df_pivot_table['Bulan Format'] = pd.to_datetime(df_pivot_table['Bulan'], errors='coerce').dt.strftime('%b %Y')
df_pivot_table['Δ Saham'] = df_pivot_table['Δ Saham'].astype(int)
df_pivot_table['Jumlah Saham'] = df_pivot_table['Jumlah Saham'].astype(int)
df_pivot_table['Persentase'] = df_pivot_table['Persentase'].map(lambda x: f"{x:.2f}%")
df_pivot_table = df_pivot_table[['Kategori Lengkap', 'Bulan Format', 'Δ Saham', 'Jumlah Saham', 'Persentase']]
tampilkan_pivot_excel(df_pivot_table, selected_code)

# 🗞️ Berita saham
st.subheader(f"🗞️ Berita Terkait Saham `{selected_code}`")
st.caption(f"📌 Kata kunci pencarian berita: `{keyword_cari}`")

for item in berita:
    st.markdown(f"### [{item['judul']}]({item['link']})")
    st.caption(f"🕒 {item['pubDate']}")
    with st.expander("Lihat isi"):
        isi = ambil_isi_berita(item['link'])
        st.markdown(isi or "❌ Tidak ada konten yang bisa ditampilkan.")
