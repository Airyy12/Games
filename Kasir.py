import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database import load_data, save_data, update_stok_barang, get_keuntungan_data, get_transaksi_data
from login import login_page
import plotly.express as px
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(page_title="Aplikasi Kasir", layout="wide")
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .sidebar .css-1d391kg { background-color: #1e1e2f !important; }
    .keuntungan-box {
        padding: 1rem;
        background-color: #1f2937;
        color: white;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Data barang (contoh)
barang_df = load_data()

# Login
login_info = login_page()
if not login_info["login"]:
    st.stop()

role = login_info["role"]

# Sidebar navigasi
with st.sidebar:
    selected = option_menu("Navigasi", ["Input Barang", "Kasir", "Struk & Riwayat", "Dashboard", "Ekspor Data"],
                           icons=["box", "cart", "file-earmark-text", "bar-chart", "cloud-arrow-down"],
                           menu_icon="menu-up", default_index=1,
                           styles={
                               "container": {"padding": "5px", "background-color": "#111827"},
                               "icon": {"color": "white", "font-size": "18px"},
                               "nav-link": {"font-size": "16px", "text-align": "left", "margin": "5px"},
                               "nav-link-selected": {"background-color": "#EF4444", "color": "white"},
                           })

# ============================== INPUT BARANG ============================== #
if selected == "Input Barang":
    st.markdown("### 📦 Input Barang Baru")
    nama = st.text_input("Nama Barang")
    kategori = st.text_input("Kategori")
    harga_modal = st.number_input("Harga Modal", min_value=0)
    harga_jual = st.number_input("Harga Jual", min_value=0)
    stok = st.number_input("Stok", min_value=0)

    if st.button("Simpan Barang"):
        new_data = pd.DataFrame([[nama, kategori, harga_modal, harga_jual, stok]],
                                 columns=["nama", "kategori", "harga_modal", "harga_jual", "stok"])
        barang_df = pd.concat([barang_df, new_data], ignore_index=True)
        save_data(barang_df)
        st.success("Barang berhasil disimpan!")

# ============================== KASIR ============================== #
elif selected == "Kasir":
    st.markdown("### 🛒 Transaksi Kasir")
    kategori_list = barang_df['kategori'].unique().tolist()
    kategori = st.selectbox("Pilih Kategori:", kategori_list)

    barang_terpilih_df = barang_df[barang_df['kategori'] == kategori]
    pilihan_barang = st.multiselect("Pilih Barang:", barang_terpilih_df['nama'].tolist())

    jumlah_barang = {}
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Jumlah Barang")
        for barang in pilihan_barang:
            jumlah_barang[barang] = st.number_input(f"Jumlah '{barang}'", min_value=1, step=1, key=barang)

    with col2:
        st.markdown("#### Status Stok Barang")
        for barang in pilihan_barang:
            stok = barang_df[barang_df['nama'] == barang]['stok'].values[0]
            if stok <= 0:
                st.error(f"'{barang}' habis!")
            elif stok < jumlah_barang[barang]:
                st.warning(f"'{barang}' stok kurang ({stok} tersisa)")
            else:
                st.success(f"'{barang}' tersedia ({stok})")

    st.markdown("### 🧾 Ringkasan Belanja")
    if st.button("Proses Transaksi"):
        total = 0
        transaksi_list = []
        for barang in jumlah_barang:
            df_row = barang_df[barang_df['nama'] == barang]
            harga = df_row['harga_jual'].values[0]
            jumlah = jumlah_barang[barang]
            total += harga * jumlah
            update_stok_barang(barang, -jumlah)
            transaksi_list.append({"barang": barang, "jumlah": jumlah, "total": harga * jumlah})
        st.success(f"Transaksi berhasil. Total: Rp{total:,}")

# ============================== STRUK & RIWAYAT ============================== #
elif selected == "Struk & Riwayat":
    st.markdown("### 📜 Riwayat Transaksi")
    transaksi_df = get_transaksi_data()
    if not transaksi_df.empty:
        st.dataframe(transaksi_df, use_container_width=True)
    else:
        st.info("Belum ada transaksi.")

# ============================== DASHBOARD ============================== #
elif selected == "Dashboard":
    st.markdown("### 📊 Dashboard Penjualan")
    tab1, tab2 = st.tabs(["📋 Tabel Keuntungan", "📈 Grafik"])

    df_keuntungan_barang, df_keuntungan_kategori, total_untung = get_keuntungan_data()

    with tab1:
        st.markdown('<div class="keuntungan-box">Total Keuntungan: Rp {:,}</div>'.format(total_untung), unsafe_allow_html=True)
        st.markdown("#### Keuntungan per Barang")
        st.dataframe(df_keuntungan_barang, use_container_width=True)

        st.markdown("#### Keuntungan per Kategori")
        st.dataframe(df_keuntungan_kategori, use_container_width=True)

    with tab2:
        fig = px.bar(df_keuntungan_barang, x='nama', y='keuntungan', title='Keuntungan per Barang')
        st.plotly_chart(fig, use_container_width=True)

# ============================== EKSPOR DATA ============================== #
elif selected == "Ekspor Data":
    st.markdown("### 📁 Ekspor Data")
    df_keuntungan_barang, df_keuntungan_kategori, _ = get_keuntungan_data()
    transaksi_df = get_transaksi_data()

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        barang_df.to_excel(writer, sheet_name="Data Barang", index=False)
        df_keuntungan_barang.to_excel(writer, sheet_name="Keuntungan Barang", index=False)
        df_keuntungan_kategori.to_excel(writer, sheet_name="Keuntungan Kategori", index=False)
        transaksi_df.to_excel(writer, sheet_name="Riwayat Transaksi", index=False)

    st.download_button("📥 Unduh Laporan Excel", data=excel_buffer.getvalue(), file_name="laporan_kasir.xlsx")
