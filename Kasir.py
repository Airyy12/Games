import streamlit as st
import pandas as pd

st.set_page_config(page_title="Aplikasi Kasir Toko", layout="wide")

st.title("🛍️ Aplikasi Kasir Toko Sederhana")

# Inisialisasi session state untuk menyimpan data barang
if "barang" not in st.session_state:
    st.session_state.barang = []

st.header("📦 Input Data Barang")

with st.form("input_barang"):
    nama = st.text_input("Nama Barang")
    harga_jual = st.number_input("Harga Jual (Rp)", min_value=0)
    harga_modal = st.number_input("Harga Modal (Rp)", min_value=0)
    stok = st.number_input("Stok Barang", min_value=0, step=1)
    submitted = st.form_submit_button("Tambah Barang")
    if submitted and nama:
        st.session_state.barang.append({
            "nama": nama,
            "harga_jual": harga_jual,
            "harga_modal": harga_modal,
            "stok": stok,
            "terjual": 0
        })
        st.success(f"Barang '{nama}' berhasil ditambahkan!")

# Tampilkan daftar barang
if st.session_state.barang:
    st.subheader("📋 Daftar Barang Tersedia")
    df_barang = pd.DataFrame(st.session_state.barang)
    st.dataframe(df_barang[["nama", "harga_jual", "stok"]])

    st.header("🛒 Simulasi Pembelian")
    pilihan_barang = [b["nama"] for b in st.session_state.barang]
    pilih = st.selectbox("Pilih Barang", pilihan_barang)
    jumlah_beli = st.number_input("Jumlah Beli", min_value=1, step=1)

    if st.button("Proses Pembelian"):
        for b in st.session_state.barang:
            if b["nama"] == pilih:
                if jumlah_beli <= b["stok"]:
                    b["stok"] -= jumlah_beli
                    b["terjual"] += jumlah_beli
                    total = jumlah_beli * b["harga_jual"]
                    st.success(f"Total Bayar: Rp {total:,}")
                else:
                    st.warning("Stok tidak mencukupi!")

    st.header("📈 Laporan Keuntungan")
    laporan = []
    total_keuntungan = 0
    for b in st.session_state.barang:
        keuntungan_per_barang = (b["harga_jual"] - b["harga_modal"]) * b["terjual"]
        laporan.append({
            "Nama": b["nama"],
            "Terjual": b["terjual"],
            "Keuntungan": keuntungan_per_barang
        })
        total_keuntungan += keuntungan_per_barang

    df_laporan = pd.DataFrame(laporan)
    st.dataframe(df_laporan)
    st.metric("💰 Total Keuntungan", f"Rp {total_keuntungan:,}")
