import pandas as pd
import streamlit as st
import plotly.express as px
import glob
import os

# ✅ Konfigurasi halaman
st.set_page_config(layout='wide', page_title="Dashboard Kepemilikan Saham")

st.title("📊 Dashboard Kepemilikan Saham Per Bulan")
st.markdown("📅 Analisis distribusi investor lokal dan asing berdasarkan data bulanan dari file `.txt` KSEI")

# 📚 Mapping kategori investor
investor_mapping = {
    'ID': 'Individual',
    'CP': 'Corporate (Perusahaan)',
    'MF': 'Mutual Fund (Reksa Dana)',
    'IB': 'Financial Institution (Lembaga Keuangan)',
    'IS': 'Insurance (Asuransi)',
    'SC': 'Securities Company (Perusahaan Efek)',
    'PF': 'Pension Fund (Dana Pensiun)',
    'FD': 'Foundation (Yayasan)',
    'OT': 'Others (Lainnya)'
}

# 📂 Ambil file dari folder
path = 'data/'
files = glob.glob(os.path.join(path, '*.txt'))

if not files:
    st.warning("Belum ada file di folder 'data/'. Upload file .txt bulanan.")
    st.stop()

df_list = []
for f in files:
    try:
        temp_df = pd.read_csv(f, sep='|')
        temp_df['Bulan'] = pd.to_datetime(temp_df['Date'], dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
        df_list.append(temp_df)
    except Exception as e:
        st.error(f"Gagal membaca file: {f}\n{e}")

df = pd.concat(df_list, ignore_index=True)

# Pilih kode saham
selected_code = st.selectbox("📌 Pilih Kode Saham", sorted(df['Code'].unique()))
df_code = df[df['Code'] == selected_code].copy()

local_cols = ['Local IS','Local CP','Local PF','Local IB','Local ID','Local MF','Local SC','Local FD','Local OT']
foreign_cols = ['Foreign IS','Foreign CP','Foreign PF','Foreign IB','Foreign ID','Foreign MF','Foreign SC','Foreign FD','Foreign OT']

df_code['Total Lokal'] = df_code[local_cols].sum(axis=1)
df_code['Total Asing'] = df_code[foreign_cols].sum(axis=1)

# 📈 Ringkasan bulanan
df_summary = df_code.groupby('Bulan')[['Total Lokal', 'Total Asing', 'Total']].sum().reset_index()
st.subheader(f"📈 Tren Kepemilikan Saham - {selected_code}")
st.line_chart(df_summary.set_index('Bulan'))

# 🥧 Komposisi terakhir
st.subheader("📊 Komposisi Lokal vs Asing di Bulan Terakhir")
latest_month = df_summary['Bulan'].max()
latest_data = df_summary[df_summary['Bulan'] == latest_month]

if not latest_data.empty:
    df_pie = latest_data.melt(id_vars='Bulan', value_vars=['Total Lokal', 'Total Asing'])
    fig_pie = px.pie(df_pie, names='variable', values='value', title=f"Komposisi Kepemilikan ({latest_month})")
    st.plotly_chart(fig_pie, use_container_width=True)

# 📋 Tabel ringkasan
st.subheader("📋 Data Ringkasan Bulanan")
st.dataframe(df_summary, use_container_width=True)

# 🔁 Transform jadi long format
df_local = df_code.melt(id_vars=['Bulan', 'Total'], value_vars=local_cols, var_name='Kategori', value_name='Jumlah Saham')
df_local['Tipe'] = 'Local'

df_foreign = df_code.melt(id_vars=['Bulan', 'Total'], value_vars=foreign_cols, var_name='Kategori', value_name='Jumlah Saham')
df_foreign['Tipe'] = 'Foreign'

df_all = pd.concat([df_local, df_foreign])
df_all = df_all[df_all['Bulan'] == latest_month].copy()
df_all['Kode'] = df_all['Kategori'].str.extract(r'(ID|CP|MF|IB|IS|SC|PF|FD|OT)')
df_all['Kategori Lengkap'] = df_all['Kode'].map(investor_mapping)
df_all['Persentase'] = (df_all['Jumlah Saham'] / df_all['Total']) * 100

# 📊 Bar Chart
st.subheader(f"📑 Rincian Kepemilikan per Kategori - {latest_month}")
fig_bar = px.bar(df_all, x='Kategori Lengkap', y='Jumlah Saham', color='Tipe', barmode='group')
st.plotly_chart(fig_bar, use_container_width=True)
st.dataframe(df_all[['Tipe', 'Kategori Lengkap', 'Jumlah Saham', 'Persentase']], use_container_width=True)

# 📉 Perbandingan Bulanan
st.subheader("📉 Perbandingan Bulanan per Kategori Investor")

df_trend = pd.concat([df_local, df_foreign])
df_trend['Kode'] = df_trend['Kategori'].str.extract(r'(ID|CP|MF|IB|IS|SC|PF|FD|OT)')
df_trend['Kategori Lengkap'] = df_trend['Kode'].map(investor_mapping)
df_trend = df_trend.groupby(['Bulan', 'Kode', 'Kategori Lengkap'])[['Jumlah Saham', 'Total']].sum().reset_index()

df_trend['Δ Saham'] = df_trend.groupby(['Kode'])['Jumlah Saham'].diff().fillna(0).astype(int)
df_trend['Persentase'] = (df_trend['Jumlah Saham'] / df_trend['Total']) * 100
df_trend['Status'] = df_trend['Δ Saham'].apply(lambda x: '⬆️ Naik' if x > 0 else ('⬇️ Turun' if x < 0 else '⏸️ Stabil'))

def format_million(val):
    return f"{val:,.0f}"

df_trend_display = df_trend.copy()
df_trend_display['Jumlah Saham'] = df_trend_display['Jumlah Saham'].apply(format_million)
df_trend_display['Δ Saham'] = df_trend_display['Δ Saham'].apply(format_million)
df_trend_display['Total'] = df_trend_display['Total'].apply(format_million)
df_trend_display['Persentase'] = df_trend_display['Persentase'].map('{:.2f}%'.format)

st.dataframe(
    df_trend_display[['Bulan', 'Kategori Lengkap', 'Δ Saham', 'Jumlah Saham', 'Persentase', 'Status']],
    use_container_width=True
)

# 📊 Format Tabel Horizontal Gaya Excel PANI
st.subheader("📊 Tabel Gaya Excel - Perubahan Tiap Bulan per Kategori Investor")

# Salin dari df_trend
df_excel = df_trend.copy()
df_excel['Bulan Format'] = pd.to_datetime(df_excel['Bulan']).dt.strftime('%b')  # e.g. 'Apr'
df_excel['Δ Saham'] = df_excel['Δ Saham'].astype('int64')
df_excel['Jumlah Saham'] = df_excel['Jumlah Saham'].astype('int64')
df_excel['Persentase'] = df_excel['Persentase'].round(2)

# Format isi sel tabel gaya PANI
df_excel['Label'] = (
    df_excel['Δ Saham'].apply(lambda x: f"{x:+,}") + "\n" +
    df_excel['Jumlah Saham'].apply(lambda x: f"{x:,}") + "\n" +
    df_excel['Persentase'].astype(str) + "%"
)

# Pivot ke bentuk horizontal: baris = kategori, kolom = bulan
pivot_excel = df_excel.pivot(index='Kategori Lengkap', columns='Bulan Format', values='Label')
pivot_excel = pivot_excel.fillna("—")  # Kosongkan yang tidak tersedia

# Fungsi highlight warna untuk Δ Saham
def highlight_change(val):
    if isinstance(val, str) and val != "—":
        delta_line = val.split('\n')[0]
        if delta_line.startswith('+'):
            return 'color: green'
        elif delta_line.startswith('-'):
            return 'color: red'
    return ''

styled = pivot_excel.style.applymap(highlight_change)
styled = styled.set_properties(**{'white-space': 'pre'})  # agar line-break tidak terpotong

# Tampilkan tabel dengan warna
st.dataframe(styled, use_container_width=True)

# 📥 Tombol Download ke Excel
import io
excel_buffer = io.BytesIO()
pivot_excel.to_excel(excel_buffer, sheet_name="Rekap Gaya PANI", index=True)
excel_buffer.seek(0)

st.download_button(
    label="📥 Download Format Tabel Excel PANI",
    data=excel_buffer,
    file_name=f"Rekap_GayaPANI_{selected_code}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# 📘 Penjelasan
with st.expander("📘 Penjelasan Tipe Investor"):
    for kode, desc in investor_mapping.items():
        st.markdown(f"**{kode}** — {desc}")
