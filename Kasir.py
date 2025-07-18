import streamlit as st
import pandas as pd

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

if "barang" not in st.session_state:
    st.session_state.barang = []

tab1, tab2, tab3 = st.tabs(["📦 Masukkan Barang", "🛒 Pembelian", "📈 Keuntungan"])

# =============================
# 📦 TAB 1: Input Data Barang
# =============================
with tab1:
    st.header("📦 Tambah Data Barang")
    with st.form("form_barang"):
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori Barang", placeholder="Contoh: Alat Tulis, Minuman")
        harga_jual = st.number_input("Harga Jual (Rp)", min_value=0)
        harga_modal = st.number_input("Harga Modal (Rp)", min_value=0)
        stok = st.number_input("Stok Barang", min_value=0, step=1)
        submit = st.form_submit_button("➕ Tambah Barang")

        if submit and nama and kategori:
            st.session_state.barang.append({
                "nama": nama,
                "kategori": kategori,
                "harga_jual": harga_jual,
                "harga_modal": harga_modal,
                "stok": stok,
                "terjual": 0
            })
            st.success(f"Barang '{nama}' berhasil ditambahkan!")

    if st.session_state.barang:
        st.subheader("📋 Daftar Barang")
        df = pd.DataFrame(st.session_state.barang)
        st.dataframe(df[["nama", "kategori", "harga_jual", "stok"]])

# =============================
# 🛒 TAB 2: Kasir / Pembelian
# =============================
with tab2:
    st.header("🛒 Simulasi Pembelian Kasir")

    if not st.session_state.barang:
        st.warning("Belum ada barang.")
    else:
        df = pd.DataFrame(st.session_state.barang)
        kategori_terpilih = st.selectbox("Filter Kategori", options=["Semua"] + sorted(df['kategori'].unique().tolist()))
        
        if kategori_terpilih != "Semua":
            df = df[df["kategori"] == kategori_terpilih]

        keyword = st.text_input("🔍 Cari Nama Barang")
        if keyword:
            df = df[df["nama"].str.contains(keyword, case=False)]

        if df.empty:
            st.info("Tidak ada barang ditemukan.")
        else:
            pilih_nama = st.selectbox("Pilih Barang", df["nama"].tolist())
            jumlah_beli = st.number_input("Jumlah Beli", min_value=1, step=1)

            barang_dipilih = next(b for b in st.session_state.barang if b["nama"] == pilih_nama)

            if st.button("🧾 Proses Pembayaran"):
                if jumlah_beli > barang_dipilih["stok"]:
                    st.error("Stok tidak cukup!")
                else:
                    total = jumlah_beli * barang_dipilih["harga_jual"]
                    barang_dipilih["stok"] -= jumlah_beli
                    barang_dipilih["terjual"] += jumlah_beli

                    st.success(f"Total belanja: Rp {total:,}")
                    bayar = st.number_input("Masukkan Uang Bayar (Rp)", min_value=0, step=1000, key="bayar")

                    if bayar >= total:
                        kembalian = bayar - total
                        st.success(f"Kembalian: Rp {kembalian:,}")
                    else:
                        st.error("Uang tidak cukup untuk membayar!")

# =============================
# 📈 TAB 3: Laporan Keuntungan
# =============================
with tab3:
    st.header("📈 Laporan Keuntungan")

    if not st.session_state.barang:
        st.warning("Belum ada transaksi.")
    else:
        laporan = []
        total_untung = 0
        for b in st.session_state.barang:
            untung = (b["harga_jual"] - b["harga_modal"]) * b["terjual"]
            laporan.append({
                "Nama": b["nama"],
                "Kategori": b["kategori"],
                "Terjual": b["terjual"],
                "Keuntungan": untung
            })
            total_untung += untung

        df_laporan = pd.DataFrame(laporan)
        st.dataframe(df_laporan)
        st.metric("💰 Total Keuntungan", f"Rp {total_untung:,}")
