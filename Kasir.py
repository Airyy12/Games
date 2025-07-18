import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_option_menu import option_menu

# ---------- Konstanta ----------
DATA_BARANG = 'data_barang.csv'
DATA_TRANSAKSI = 'data_transaksi.csv'
DATA_USER = 'data_user.csv'

st.set_page_config(layout="wide")

# ---------- Helper Function ----------
def load_data(file_path, default_columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=default_columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# ---------- Inisialisasi Data ----------
barang_df = load_data(DATA_BARANG, ['nama', 'kategori', 'harga_modal', 'harga_jual', 'stok'])
transaksi_df = load_data(DATA_TRANSAKSI, ['nama', 'jumlah', 'harga_modal', 'harga_jual', 'kategori', 'tanggal'])
user_df = load_data(DATA_USER, ['username', 'password', 'role'])

# ---------- Session State ----------
if 'login' not in st.session_state:
    st.session_state.login = False
if 'role' not in st.session_state:
    st.session_state.role = ''
if 'username' not in st.session_state:
    st.session_state.username = ''

# ---------- Login & Registrasi ----------
def login_page():
    st.markdown("## 🔐 Login Kasir")

    menu = ["Login", "Buat Akun"]
    choice = st.radio("Pilih Menu:", menu, horizontal=True)

    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk"):
            user = user_df[(user_df.username == username) & (user_df.password == password)]
            if not user.empty:
                st.session_state.login = True
                st.session_state.role = user.iloc[0]['role']
                st.session_state.username = username
                st.success(f"Berhasil login sebagai {st.session_state.role}")
            else:
                st.error("Username atau password salah")

    elif choice == "Buat Akun":
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password", type="password")
        new_role = st.radio("Pilih Role:", ["admin", "kasir"], horizontal=True)
        if st.button("Daftar"):
            if new_user in user_df['username'].values:
                st.warning("Username sudah digunakan")
            else:
                user_df.loc[len(user_df)] = [new_user, new_pass, new_role]
                save_data(user_df, DATA_USER)
                st.success("Akun berhasil dibuat, silakan login")

# ---------- Halaman Transaksi ----------
def halaman_kasir():
    tab1, tab2 = st.tabs(["\U0001F6D2 Transaksi", "🪚 Status Stok Barang"])

    with tab1:
        st.subheader("Pilih Kategori:")
        kategori = st.selectbox("", barang_df['kategori'].unique())

        st.subheader("Pilih Barang:")
        barang_list = st.multiselect("", barang_df[barang_df['kategori'] == kategori]['nama'].tolist())

        jumlah_dict = {}
        for barang in barang_list:
            jumlah_dict[barang] = st.number_input(f"Jumlah '{barang}'", min_value=1, value=1, step=1, key=barang)

        if st.button("Simpan Transaksi"):
            for barang in barang_list:
                data = barang_df[barang_df['nama'] == barang].iloc[0]
                transaksi_df.loc[len(transaksi_df)] = [
                    barang,
                    jumlah_dict[barang],
                    data['harga_modal'],
                    data['harga_jual'],
                    data['kategori'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                # Kurangi stok
                barang_df.loc[barang_df['nama'] == barang, 'stok'] -= jumlah_dict[barang]

            save_data(transaksi_df, DATA_TRANSAKSI)
            save_data(barang_df, DATA_BARANG)
            st.success("Transaksi berhasil disimpan.")

    with tab2:
        st.subheader("Status Stok Barang")
        stok_habis = barang_df[barang_df['stok'] <= 0]
        stok_ada = barang_df[barang_df['stok'] > 0]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚫 Habis")
            st.dataframe(stok_habis[['nama', 'kategori', 'stok']])

        with col2:
            st.markdown("### ✅ Tersedia")
            st.dataframe(stok_ada[['nama', 'kategori', 'stok']])

# ---------- Halaman Admin ----------
def halaman_admin():
    st.title("Dashboard Admin")

    total_keuntungan = ((transaksi_df['harga_jual'] - transaksi_df['harga_modal']) * transaksi_df['jumlah']).sum()
    st.markdown(f"### Total Keuntungan: Rp **:green[{int(total_keuntungan)}]**")

    keuntungan_barang = transaksi_df.groupby('nama').apply(lambda df: ((df['harga_jual'] - df['harga_modal']) * df['jumlah']).sum()).reset_index(name='keuntungan')
    keuntungan_kategori = transaksi_df.groupby('kategori').apply(lambda df: ((df['harga_jual'] - df['harga_modal']) * df['jumlah']).sum()).reset_index(name='keuntungan')

    st.markdown("### Keuntungan per Barang")
    st.dataframe(keuntungan_barang)

    st.markdown("### Keuntungan per Kategori")
    st.dataframe(keuntungan_kategori)

# ---------- Main ----------
if not st.session_state.login:
    login_page()
else:
    if st.session_state.role == 'kasir':
        halaman_kasir()
    elif st.session_state.role == 'admin':
        halaman_admin()
