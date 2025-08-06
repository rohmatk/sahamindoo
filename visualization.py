import streamlit as st
import plotly.express as px
import io
import pandas as pd

 
def plot_bar_perbandingan(df_melt):
    fig = px.bar(df_melt, 
                 x='Bulan', 
                 y='Jumlah Saham', 
                 color='Jenis', 
                 facet_col='Kategori Lengkap', 
                 facet_col_wrap=3, 
                 title="Perbandingan Kepemilikan per Bulan: Lokal vs Asing",
                 height=800)
    st.plotly_chart(fig, use_container_width=True, key="bar_perbandingan")


def plot_line_trend_summary(df_summary, selected_code):
    st.subheader(f"📈 Tren Kepemilikan Saham - {selected_code}")
    st.line_chart(df_summary.set_index('Bulan'), use_container_width=True)




def tampilkan_pie_terakhir(df_summary, selected_code):
    latest_month = df_summary['Bulan'].max()
    latest_data = df_summary[df_summary['Bulan'] == latest_month]

    if not latest_data.empty:
        df_pie = latest_data.melt(id_vars='Bulan', value_vars=['Total Lokal', 'Total Asing'])
        fig = px.pie(df_pie, names='variable', values='value', title=f"Komposisi Kepemilikan ({latest_month})")
        st.plotly_chart(fig, use_container_width=True, key=f"pie_komposisi_{selected_code}")


def plot_line_per_kategori(df_plot_grouped, selected_code):
    fig = px.line(
        df_plot_grouped,
        x='Bulan',
        y='Jumlah Saham',
        color='Label',
        title=f"📈 Tren Bulanan Kategori Investor - {selected_code}",
        markers=True
    )
    fig.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Saham", legend_title="Kategori Investor")
    st.plotly_chart(fig, use_container_width=True, key=f"line-per-kategori-{selected_code}")


def plot_bar_per_kategori_terakhir(df_all_latest, selected_code, latest_month):
    fig = px.bar(
        df_all_latest,
        x='Kategori Lengkap',
        y='Jumlah Saham',
        color='Jenis',
        barmode='group',
        title=f"📊 Komposisi Kepemilikan Terakhir ({latest_month}) - {selected_code}"
    )
    st.plotly_chart(fig, use_container_width=True, key=f"bar-kategori-{selected_code}")


def tampilkan_tabel_trend_kategori(df_trend_display):
    st.dataframe(
        df_trend_display[['Bulan', 'Kategori Lengkap', 'Δ Saham', 'Jumlah Saham', 'Persentase', 'Status']],
        use_container_width=True
    )


def tampilkan_pivot_excel(df_pivot_table, selected_code):
    st.dataframe(df_pivot_table, use_container_width=True)

    excel_buffer = io.BytesIO()
    df_pivot_table.to_excel(excel_buffer, sheet_name="Pivot Multi-Kolom", index=True)
    excel_buffer.seek(0)

    st.download_button(
        label="📥 Download Tabel Multi-Kolom Excel",
        data=excel_buffer,
        file_name=f"Rekap_MultiKolom_{selected_code}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_excel_{selected_code}"
    )
