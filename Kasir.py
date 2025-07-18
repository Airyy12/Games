import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File penyimpanan
USER_FILE = "akun.csv"
BARANG_FILE = "produk.csv"
TRANSAKSI_FILE = "riwayat_transaksi.csv"

# Cek dan inisialisasi file jika belum ada
def init_files():
    if not os.path.exists(USER_FILE):
        pd.DataFrame(columns=["username", "password", "role"]).to_csv(USER_FILE, index=False)
    if not os.path.exists(BARANG_FILE):
        pd.DataFrame(columns=["nama", "kategori", "harga_modal", "harga_jual", "stok"]).to_csv(BARANG_FILE, index=False)
    if not os.path.exists(TRANSAKSI_FILE):
        pd.DataFrame(columns=["waktu", "barang", "jumlah", "total", "keuntungan"]).to_csv(TRANSAKSI_FILE, index=False)

init_files()

# Load data
df_user = pd.read_csv(USER_FILE)
df_barang = pd.read_csv(BARANG_FILE)
df_transaksi = pd.read_csv(TRANSAKSI_FILE)

# Fungsi Login
def login(username, password):
    user = df_user[(df_user['username'] == username) & (df_user['password'] == password)]
    if not user.empty:
        return user.iloc[0]['role']
    return None

# Fungsi Registrasi
def register(username, password, role):
    if username in df_user['username'].values:
        return False
    new_user = pd.DataFrame([[username, password, role]], columns=df_user.columns)
    new_user.to_csv(USER_FILE, mode='a', index=False, header=False)
    return True

# Sidebar navigasi
if "page" not in st.session_state:
    st.session_state.page = "Login"

# Halaman Login
if st.session_state.page == "Login":
    st.markdown("## 🔐 Login Kasir")
    tabs = st.tabs(["🔑 Masuk", "🆕 Daftar Akun"])

    with tabs[0]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk"):
            role = login(username, password)
            if role:
                st.session_state.page = "App"
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Login gagal. Periksa username dan password.")

    with tabs[1]:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Role", ["admin", "kasir"])
        if st.button("Daftar"):
            if register(new_user, new_pass, new_role):
                st.success("Berhasil membuat akun! Silakan login.")
            else:
                st.warning("Username sudah digunakan.")

# Halaman utama aplikasi
elif st.session_state.page == "App":
    menu = st.sidebar.radio("Navigasi", ["Input Barang", "Kasir", "Struk & Riwayat", "Dashboard", "Ekspor Data"])

    if menu == "Input Barang" and st.session_state.role == "admin":
        st.header("📦 Input Barang Baru")
        with st.form("input_form"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            harga_modal = st.number_input("Harga Modal", min_value=0)
            harga_jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok", min_value=0)
            submitted = st.form_submit_button("Simpan")

            if submitted:
                new = pd.DataFrame([[nama, kategori, harga_modal, harga_jual, stok]], columns=df_barang.columns)
                new.to_csv(BARANG_FILE, mode='a', index=False, header=False)
                st.success("Barang berhasil ditambahkan!")

    elif menu == "Kasir":
        st.header("🛍️ Transaksi Kasir")

        tab1, tab2 = st.tabs(["🛒 Transaksi", "📦 Status Stok Barang"])

        with tab1:
            kategori = st.selectbox("Pilih Kategori:", df_barang['kategori'].unique())
            items = df_barang[df_barang['kategori'] == kategori]
            selected_items = st.multiselect("Pilih Barang:", items['nama'].tolist())

            jumlah_dict = {}
            for nama_barang in selected_items:
                jumlah = st.number_input(f"Jumlah '{nama_barang}'", min_value=1, value=1, step=1)
                jumlah_dict[nama_barang] = jumlah

            if st.button("Simpan Transaksi"):
                total = 0
                keuntungan = 0
                waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for nama_barang, jumlah in jumlah_dict.items():
                    barang = df_barang[df_barang['nama'] == nama_barang].iloc[0]
                    total_harga = barang['harga_jual'] * jumlah
                    untung = (barang['harga_jual'] - barang['harga_modal']) * jumlah
                    new_row = pd.DataFrame([[waktu, nama_barang, jumlah, total_harga, untung]], columns=df_transaksi.columns)
                    new_row.to_csv(TRANSAKSI_FILE, mode='a', index=False, header=False)
                    total += total_harga
                    keuntungan += untung
                    # update stok
                    df_barang.loc[df_barang['nama'] == nama_barang, 'stok'] -= jumlah
                    df_barang.to_csv(BARANG_FILE, index=False)

                st.success(f"Total Belanja: Rp {total}")

        with tab2:
            st.subheader("❌ Barang Habis")
            habis = df_barang[df_barang['stok'] == 0]
            if habis.empty:
                st.success("Semua barang tersedia")
            else:
                st.dataframe(habis[['nama', 'stok']])

            st.subheader("✅ Barang Tersedia")
            tersedia = df_barang[df_barang['stok'] > 0]
            st.dataframe(tersedia[['nama', 'stok']])

    elif menu == "Struk & Riwayat":
        st.header("📃 Struk dan Riwayat Transaksi")
        df = pd.read_csv(TRANSAKSI_FILE)
        st.dataframe(df)

    elif menu == "Dashboard":
        st.header("📊 Dashboard Penjualan")

        keuntungan_total = df_transaksi['keuntungan'].sum()
        st.markdown(f"### 💰 Total Keuntungan: <span style='color:lime;font-size:30px'>Rp {keuntungan_total:,}</span>", unsafe_allow_html=True)

        keuntungan_barang = df_transaksi.groupby('barang')['keuntungan'].sum().reset_index()
        st.subheader("Keuntungan per Barang")
        st.dataframe(keuntungan_barang, use_container_width=True)

        df_join = df_transaksi.merge(df_barang[['nama', 'kategori']], left_on='barang', right_on='nama', how='left')
        keuntungan_kategori = df_join.groupby('kategori')['keuntungan'].sum().reset_index()
        st.subheader("Keuntungan per Kategori")
        st.dataframe(keuntungan_kategori, use_container_width=True)

    elif menu == "Ekspor Data":
        st.header("⬇️ Ekspor Data")
        csv = df_transaksi.to_csv(index=False).encode('utf-8')
        st.download_button("Download Transaksi", csv, "transaksi.csv", "text/csv")
