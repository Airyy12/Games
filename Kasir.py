import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

AKUN_FILE = "akun.json"

def load_akun():
    if not os.path.exists(AKUN_FILE):
        with open(AKUN_FILE, "w") as f:
            json.dump([], f)
    with open(AKUN_FILE, "r") as f:
        return json.load(f)

def simpan_akun(data):
    with open(AKUN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def tampilkan_login():
    st.title("🔐 Login Kasir")
    tab1, tab2 = st.tabs(["Login", "Buat Akun Baru"])

    with tab1:
        data = load_akun()
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["admin", "kasir"], horizontal=True)
        if st.button("Masuk"):
            cocok = next((a for a in data if a["username"] == username and a["password"] == password and a["role"] == role), None)
            if cocok:
                st.session_state.login = True
                st.session_state.user = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Login gagal. Periksa username/password/role.")

    with tab2:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Pilih Role", ["admin", "kasir"], horizontal=True, key="daftar")
        if st.button("Daftar"):
            data = load_akun()
            if any(u["username"] == new_user for u in data):
                st.warning("Username sudah ada.")
            else:
                data.append({"username": new_user, "password": new_pass, "role": new_role})
                simpan_akun(data)
                st.success("Akun berhasil dibuat!")

if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

if "barang" not in st.session_state:
    st.session_state.barang = []
if "transaksi" not in st.session_state:
    st.session_state.transaksi = []

st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("🔒 Logout"):
    st.session_state.clear()
    st.rerun()

# Tabs
menu = ["📦 Input Barang", "🛒 Kasir", "📋 Stok", "🧾 Riwayat", "📈 Dashboard", "📤 Ekspor"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(menu)

with tab1:
    st.header("📦 Input Barang")
    if st.session_state.role != "admin":
        st.warning("Hanya admin yang bisa menambahkan barang.")
    else:
        with st.form("form_barang"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            modal = st.number_input("Harga Modal", min_value=0)
            jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok Awal", min_value=0, step=1)
            simpan = st.form_submit_button("Simpan Barang")
            if simpan and nama and kategori:
                st.session_state.barang.append({
                    "nama": nama,
                    "kategori": kategori,
                    "harga_modal": modal,
                    "harga_jual": jual,
                    "stok": stok,
                    "terjual": 0
                })
                st.success(f"Barang '{nama}' disimpan.")

        if st.session_state.barang:
            st.dataframe(pd.DataFrame(st.session_state.barang))

with tab2:
    st.header("🛒 Transaksi Kasir (Versi Dropdown)")

    if not st.session_state.barang:
        st.warning("Belum ada barang di stok.")
    else:
        df_barang = pd.DataFrame(st.session_state.barang)

        # Pilih Kategori
        kategori_list = df_barang["kategori"].unique().tolist()
        kategori_pilih = st.selectbox("Pilih Kategori:", kategori_list)

        # Filter barang sesuai kategori
        df_kategori = df_barang[df_barang["kategori"] == kategori_pilih]

        # Pilih Barang
        nama_barang_list = df_kategori["nama"].tolist()
        barang_pilih = st.selectbox("Pilih Barang:", nama_barang_list)

        # Ambil data barang terpilih
        barang_data = df_kategori[df_kategori["nama"] == barang_pilih].iloc[0]

        # Input jumlah beli
        jumlah_beli = st.number_input(f"Jumlah '{barang_pilih}'", 
                                      min_value=1, 
                                      max_value=int(barang_data["stok"]),
                                      step=1)

        # Simpan Transaksi
        if st.button("Simpan Transaksi"):
            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update stok & transaksi
            for b in st.session_state.barang:
                if b["nama"] == barang_pilih:
                    b["stok"] -= jumlah_beli
                    b["terjual"] += jumlah_beli

                    keuntungan = (b["harga_jual"] - b["harga_modal"]) * jumlah_beli
                    total = b["harga_jual"] * jumlah_beli

                    st.session_state.transaksi.append({
                        "waktu": waktu,
                        "nama": b["nama"],
                        "kategori": b["kategori"],
                        "jumlah": jumlah_beli,
                        "total": total,
                        "keuntungan": keuntungan
                    })

            st.success("Transaksi berhasil disimpan.")

with tab3:
    st.header("📋 Status Stok Barang")
    if not st.session_state.barang:
        st.info("Belum ada barang.")
    else:
        df = pd.DataFrame(st.session_state.barang)
        kosong = df[df["stok"] == 0]
        tersedia = df[df["stok"] > 0]
        st.subheader("Barang Habis")
        if kosong.empty:
            st.success("Tidak ada barang yang habis.")
        else:
            st.dataframe(kosong)
        st.subheader("Barang Masih Tersedia")
        st.dataframe(tersedia)

with tab4:
    st.header("🧾 Riwayat Transaksi")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df)

with tab5:
    st.header("📈 Dashboard")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df = pd.DataFrame(st.session_state.transaksi)
        tab_a, tab_b = st.tabs(["📊 Grafik", "📋 Tabel"])
        with tab_a:
            fig1 = px.bar(df.groupby("nama")["jumlah"].sum().reset_index(), x="nama", y="jumlah", title="Penjualan per Barang")
            fig2 = px.pie(df, names="nama", values="keuntungan", title="Kontribusi Keuntungan")
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
        with tab_b:
            st.dataframe(df.groupby("nama")[["jumlah", "keuntungan"]].sum().reset_index())

with tab6:
    st.header("📤 Ekspor Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.barang:
            df = pd.DataFrame(st.session_state.barang)
            st.download_button("⬇️ Unduh Barang", df.to_csv(index=False), file_name="barang.csv")
    with col2:
        if st.session_state.transaksi:
            df = pd.DataFrame(st.session_state.transaksi)
            st.download_button("⬇️ Unduh Transaksi", df.to_csv(index=False), file_name="transaksi.csv")
