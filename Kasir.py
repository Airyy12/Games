import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils import *

# Init DB
init_db()

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

# Login system
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔒 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM akun WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password(password, user["password"]):
            st.session_state.login = True
            st.session_state.user = username
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Login gagal.")

# Load barang & transaksi
conn = get_db_connection()
barang_df = pd.read_sql_query("SELECT * FROM barang", conn)
transaksi_df = pd.read_sql_query("SELECT * FROM transaksi", conn)
conn.close()

# Sidebar
st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# Tabs
tabs = st.tabs(["📦 Barang", "🛒 Kasir", "📋 Stok", "🧾 Riwayat", "📊 Dashboard", "📤 Ekspor"])

# 📦 Barang Admin
with tabs[0]:
    st.header("📦 Manajemen Barang")
    if st.session_state.role != "admin":
        st.warning("Hanya admin yang bisa mengelola barang.")
    else:
        with st.form("form_barang"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            harga_modal = st.number_input("Harga Modal", min_value=0.0)
            harga_jual = st.number_input("Harga Jual", min_value=0.0)
            stok = st.number_input("Stok Awal", min_value=0, step=1)
            stok_minimum = st.number_input("Stok Minimum (Notifikasi)", min_value=1, value=5)
            simpan = st.form_submit_button("💾 Simpan")
            if simpan and nama and kategori:
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO barang (nama, kategori, harga_modal, harga_jual, stok, stok_minimum) VALUES (?, ?, ?, ?, ?, ?)",
                    (nama, kategori, harga_modal, harga_jual, stok, stok_minimum)
                )
                conn.commit()
                conn.close()
                st.success(f"Barang '{nama}' berhasil disimpan.")
                st.rerun()

        st.subheader("📋 Daftar Barang")
        st.dataframe(barang_df)

# 🛒 Kasir
with tabs[1]:
    st.header("🛒 Transaksi Kasir")
    if barang_df.empty:
        st.warning("Belum ada barang.")
    else:
        if "keranjang" not in st.session_state:
            st.session_state.keranjang = []

        pilihan_barang = st.selectbox("Pilih Barang", barang_df["nama"])
        jumlah = st.number_input("Jumlah Beli", min_value=1, step=1)
        barang_data = barang_df[barang_df["nama"] == pilihan_barang].iloc[0]

        if st.button("Tambah ke Keranjang"):
            st.session_state.keranjang.append({
                "nama": pilihan_barang,
                "kategori": barang_data["kategori"],
                "jumlah": jumlah,
                "harga_satuan": barang_data["harga_jual"],
                "subtotal": jumlah * barang_data["harga_jual"]
            })
            st.success(f"{jumlah} {pilihan_barang} ditambahkan ke keranjang.")
            st.rerun()

        if st.session_state.keranjang:
            st.subheader("📝 Keranjang")
            st.table(pd.DataFrame(st.session_state.keranjang))
            total_bayar = sum(item["subtotal"] for item in st.session_state.keranjang)
            st.write(f"💵 Total: Rp{total_bayar:,}")
            uang_bayar = st.number_input("Uang Bayar", min_value=0, step=1000)

            if st.button("✅ Proses Transaksi"):
                if uang_bayar < total_bayar:
                    st.error("Uang tidak cukup.")
                else:
                    kembalian = uang_bayar - total_bayar
                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn = get_db_connection()
                    for item in st.session_state.keranjang:
                        # Kurangi stok
                        conn.execute(
                            "UPDATE barang SET stok = stok - ?, terjual = terjual + ? WHERE nama = ?",
                            (item["jumlah"], item["jumlah"], item["nama"])
                        )
                        # Catat transaksi
                        keuntungan = (item["harga_satuan"] - barang_df[barang_df["nama"] == item["nama"]]["harga_modal"].values[0]) * item["jumlah"]
                        conn.execute(
                            "INSERT INTO transaksi (waktu, nama, kategori, jumlah, total, keuntungan, user) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (waktu, item["nama"], item["kategori"], item["jumlah"], item["subtotal"], keuntungan, st.session_state.user)
                        )
                    conn.commit()
                    conn.close()

                    struk_pdf = generate_pdf_struk(st.session_state.keranjang, total_bayar, uang_bayar, kembalian, waktu, st.session_state.user)
                    st.success("✅ Transaksi berhasil.")
                    st.download_button("🖨️ Download Struk (PDF)", data=struk_pdf, file_name="struk.pdf")
                    st.session_state.keranjang.clear()
                    st.rerun()

# 📋 Stok
with tabs[2]:
    st.header("📋 Status Stok Barang")
    st.dataframe(barang_df)
    stok_min = barang_df[barang_df["stok"] <= barang_df["stok_minimum"]]
    if not stok_min.empty:
        st.warning("⚠️ Barang dengan stok rendah:")
        st.dataframe(stok_min)

# 🧾 Riwayat
with tabs[3]:
    st.header("🧾 Riwayat Transaksi")
    if transaksi_df.empty:
        st.info("Belum ada transaksi.")
    else:
        st.dataframe(transaksi_df)

# 📊 Dashboard
with tabs[4]:
    st.header("📊 Dashboard")
    if transaksi_df.empty:
        st.info("Belum ada data.")
    else:
        penjualan = transaksi_df.groupby("nama")["jumlah"].sum().reset_index()
        fig = px.bar(penjualan, x="nama", y="jumlah", title="Penjualan per Barang")
        st.plotly_chart(fig)

# 📤 Ekspor
with tabs[5]:
    st.header("📤 Ekspor Data")
    st.download_button("⬇️ Ekspor Barang", barang_df.to_csv(index=False), file_name="barang.csv")
    st.download_button("⬇️ Ekspor Transaksi", transaksi_df.to_csv(index=False), file_name="transaksi.csv")
