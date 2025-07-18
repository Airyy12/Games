import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime

# -----------------------------
# Helper Functions
# -----------------------------
def load_data():
    if os.path.exists("produk.csv"):
        return pd.read_csv("produk.csv")
    return pd.DataFrame(columns=['nama', 'kategori', 'harga_modal', 'harga_jual', 'stok'])

def load_transaksi():
    if os.path.exists("transaksi.csv"):
        return pd.read_csv("transaksi.csv")
    return pd.DataFrame(columns=['waktu', 'nama', 'jumlah', 'harga_jual', 'harga_modal'])

def save_transaksi(data):
    df = load_transaksi()
    df = pd.concat([df, data], ignore_index=True)
    df.to_csv("transaksi.csv", index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    if not os.path.exists("users.csv"):
        return False, None
    df = pd.read_csv("users.csv")
    hashed = hash_password(password)
    match = df[(df['username'] == username) & (df['password'] == hashed)]
    if not match.empty:
        return True, match.iloc[0]['role']
    return False, None

def create_account(username, password, role):
    df = pd.read_csv("users.csv") if os.path.exists("users.csv") else pd.DataFrame(columns=['username', 'password', 'role'])
    if username in df['username'].values:
        return False
    hashed = hash_password(password)
    df.loc[len(df)] = [username, hashed, role]
    df.to_csv("users.csv", index=False)
    return True

# -----------------------------
# Session State
# -----------------------------
if 'login' not in st.session_state:
    st.session_state.login = False
if 'role' not in st.session_state:
    st.session_state.role = None

# -----------------------------
# Login / Register
# -----------------------------
if not st.session_state.login:
    st.title("🔐 Login Kasir")
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Daftar"])

    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk"):
            valid, role = check_login(username, password)
            if valid:
                st.session_state.login = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Login gagal. Username atau password salah.")

    with tab_register:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Pilih Role:", ['admin', 'kasir'])
        if st.button("Daftar"):
            success = create_account(new_user, new_pass, new_role)
            if success:
                st.success("Akun berhasil dibuat!")
            else:
                st.error("Username sudah digunakan.")

else:
    # -----------------------------
    # Halaman Utama
    # -----------------------------
    st.sidebar.title("📚 Navigasi")
    menu = st.sidebar.radio("Pilih Halaman:", ["Input Barang", "Kasir", "Struk & Riwayat", "Dashboard", "Ekspor Data"])
    df_produk = load_data()

    # -----------------------------
    # Input Barang (admin only)
    # -----------------------------
    if menu == "Input Barang":
        if st.session_state.role != 'admin':
            st.warning("Hanya admin yang dapat mengakses halaman ini.")
        else:
            st.title("📦 Input Barang Baru")
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            harga_modal = st.number_input("Harga Modal", min_value=0)
            harga_jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok", min_value=0)
            if st.button("Simpan"):
                df_produk.loc[len(df_produk)] = [nama, kategori, harga_modal, harga_jual, stok]
                df_produk.to_csv("produk.csv", index=False)
                st.success("Barang berhasil ditambahkan!")

    # -----------------------------
    # Kasir
    # -----------------------------
    elif menu == "Kasir":
        st.title("🛍️ Transaksi Kasir")
        tab1, tab2 = st.tabs(["🛒 Transaksi", "📦 Status Stok Barang"])

        with tab1:
            kategori = st.selectbox("Pilih Kategori:", df_produk['kategori'].unique())
            barang_filtered = df_produk[df_produk['kategori'] == kategori]
            selected = st.multiselect("Pilih Barang:", barang_filtered['nama'].tolist())

            jumlah_dict = {}
            for item in selected:
                jumlah_dict[item] = st.number_input(f"Jumlah '{item}'", min_value=1, value=1, step=1)

            if st.button("Simpan Transaksi"):
                data = []
                waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for item in selected:
                    row = df_produk[df_produk['nama'] == item].iloc[0]
                    data.append({
                        'waktu': waktu,
                        'nama': item,
                        'jumlah': jumlah_dict[item],
                        'harga_jual': row['harga_jual'],
                        'harga_modal': row['harga_modal']
                    })
                save_transaksi(pd.DataFrame(data))
                st.success("Transaksi berhasil disimpan.")

        with tab2:
            st.subheader("📦 Informasi Stok")
            habis = df_produk[df_produk['stok'] == 0]
            tersedia = df_produk[df_produk['stok'] > 0]

            st.markdown("### ❌ Barang Habis")
            if habis.empty:
                st.success("Tidak ada barang yang habis.")
            else:
                st.dataframe(habis[['nama', 'stok']], use_container_width=True)

            st.markdown("### ✅ Barang Tersedia")
            st.dataframe(tersedia[['nama', 'stok']], use_container_width=True)

    # -----------------------------
    # Struk & Riwayat
    # -----------------------------
    elif menu == "Struk & Riwayat":
        st.title("🧾 Struk & Riwayat Transaksi")
        df_trx = load_transaksi()
        st.dataframe(df_trx.sort_values('waktu', ascending=False), use_container_width=True)

    # -----------------------------
    # Dashboard
    # -----------------------------
    elif menu == "Dashboard":
        st.title("📊 Dashboard Keuntungan")
        tab1, tab2 = st.tabs(["📈 Grafik", "📋 Tabel"])
        df_trx = load_transaksi()
        if df_trx.empty:
            st.info("Belum ada data transaksi.")
        else:
            df_trx['keuntungan'] = (df_trx['harga_jual'] - df_trx['harga_modal']) * df_trx['jumlah']
            total = df_trx['keuntungan'].sum()

            with tab2:
                st.markdown(f"### 💰 Total Keuntungan: <span style='font-size:24px; color:lime'>Rp {int(total):,}</span>", unsafe_allow_html=True)
                st.subheader("Keuntungan per Barang")
                st.dataframe(df_trx.groupby('nama')['keuntungan'].sum().reset_index(), use_container_width=True)

                st.subheader("Keuntungan per Kategori")
                merged = df_trx.merge(df_produk[['nama', 'kategori']], on='nama', how='left')
                st.dataframe(merged.groupby('kategori')['keuntungan'].sum().reset_index(), use_container_width=True)

            with tab1:
                # Implementasi grafik bisa ditambahkan dengan matplotlib/seaborn/plotly
                st.info("Fitur grafik menyusul...")

    # -----------------------------
    # Ekspor Data
    # -----------------------------
    elif menu == "Ekspor Data":
        st.title("📤 Ekspor Data")
        df_trx = load_transaksi()
        if not df_trx.empty:
            st.download_button("💾 Unduh CSV", df_trx.to_csv(index=False), "transaksi.csv")
        else:
            st.info("Belum ada data untuk diekspor.")
