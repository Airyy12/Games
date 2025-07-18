import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Load Data Produk
DATA_FILE = "produk.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["nama", "kategori", "harga_modal", "harga_jual", "stok"])

# Header Aplikasi
st.set_page_config(page_title="Aplikasi Kasir", layout="wide")
st.title("🛍️ Transaksi Kasir")

# Tabs untuk Transaksi & Status Stok
transaksi_tab, stok_tab = st.tabs(["🛒 Transaksi", "📦 Status Stok Barang"])

with transaksi_tab:
    st.markdown("### Pilih Kategori:")
    kategori_list = df["kategori"].dropna().unique().tolist()
    if not kategori_list:
        st.warning("Tidak ada kategori tersedia.")
    else:
        selected_kategori = st.selectbox("Kategori:", kategori_list)
        filtered_df = df[df["kategori"] == selected_kategori]

        barang_list = filtered_df["nama"].tolist()
        selected_barang = st.multiselect("Pilih Barang:", barang_list)

        jumlah_dict = {}
        for barang in selected_barang:
            jumlah = st.number_input(
                f"Jumlah '{barang}'",
                min_value=1,
                value=1,
                step=1,
                key=f"jumlah_{barang}"
            )
            jumlah_dict[barang] = jumlah

        if jumlah_dict:
            st.markdown("---")
            st.subheader("📋 Ringkasan Belanja")
            ringkasan = []
            total_harga = 0
            for barang, jumlah in jumlah_dict.items():
                row = df[df["nama"] == barang].iloc[0]
                subtotal = row["harga_jual"] * jumlah
                total_harga += subtotal
                ringkasan.append({
                    "Barang": barang,
                    "Jumlah": jumlah,
                    "Harga Satuan": row["harga_jual"],
                    "Subtotal": subtotal
                })
            st.dataframe(pd.DataFrame(ringkasan))
            st.success(f"Total Bayar: Rp {total_harga:,}")

with stok_tab:
    st.markdown("### 🔎 Status Stok Barang")
    barang_habis = df[df['stok'] == 0]
    barang_tersedia = df[df['stok'] > 0]

    st.subheader("❌ Barang Habis")
    if barang_habis.empty:
        st.success("Semua barang masih tersedia!")
    else:
        st.dataframe(barang_habis[['nama', 'stok']], use_container_width=True)

    st.subheader("✅ Barang Tersedia")
    st.dataframe(barang_tersedia[['nama', 'stok']], use_container_width=True)

# Catatan: Pastikan produk.csv memiliki kolom: nama, kategori, harga_modal, harga_jual, stok
