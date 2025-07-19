# aplikasi_kasir.py
import streamlit as st
import pandas as pd
import json
import os
import bcrypt
import plotly.express as px
from fpdf import FPDF
import qrcode
from PIL import Image
from datetime import datetime
import io

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

# ------------------- File Paths ------------------- #
AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"
KATEGORI_FILE = "kategori.json"

# ------------------- Helper Functions ------------------- #
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def login_user():
    st.title("🔐 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        akun_data = load_data(AKUN_FILE)
        for akun in akun_data:
            if akun["username"] == username and bcrypt.checkpw(password.encode(), akun["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = akun.get("role", "kasir")
                st.rerun()
        st.error("Username atau password salah.")

def register_user():
    if st.session_state.get("role") != "admin":
        st.warning("❌ Hanya admin yang dapat mendaftarkan user baru.")
        return

    st.subheader("📝 Registrasi User Baru (Admin Only)")
    new_username = st.text_input("Username Baru", key="reg_user")
    new_password = st.text_input("Password Baru", type="password", key="reg_pass")
    confirm_password = st.text_input("Konfirmasi Password", type="password", key="reg_confirm")
    role = st.selectbox("Pilih Role", ["kasir", "admin"])

    if st.button("Daftar"):
        if new_password != confirm_password:
            st.error("Password dan konfirmasi tidak cocok.")
        elif not new_username or not new_password:
            st.warning("Username dan Password wajib diisi.")
        else:
            akun = load_data(AKUN_FILE)
            if any(user["username"] == new_username for user in akun):
                st.warning("Username sudah digunakan.")
            else:
                hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                akun.append({
                    "username": new_username,
                    "password": hashed_pw,
                    "role": role
                })
                save_data(AKUN_FILE, akun)
                st.success(f"Akun dengan role '{role}' berhasil didaftarkan.")

def main_menu():
    st.sidebar.title(f"Selamat datang, {st.session_state.username} ({st.session_state.role})")
    menu = st.sidebar.radio("Menu", ["Transaksi", "Stok Barang", "Laporan", "Kategori"] + (["Registrasi User"] if st.session_state.role == "admin" else []) + ["Logout"])

    if menu == "Logout":
        st.session_state.clear()
        st.rerun()
    elif menu == "Registrasi User":
        register_user()
    elif menu == "Kategori":
        kategori_page()
    elif menu == "Stok Barang":
        barang_page()
    elif menu == "Transaksi":
        transaksi_page()
    elif menu == "Laporan":
        laporan_page()

# ------------------- Pages ------------------- #
def kategori_page():
    st.subheader("📦 Manajemen Kategori Barang")
    kategori_data = load_data(KATEGORI_FILE)

    new_kat = st.text_input("Kategori Baru")
    if st.button("Tambah Kategori"):
        if new_kat and new_kat not in kategori_data:
            kategori_data.append(new_kat)
            save_data(KATEGORI_FILE, kategori_data)
            st.success("Kategori berhasil ditambahkan.")

    st.write("### Daftar Kategori")
    st.write(kategori_data)

def barang_page():
    st.subheader("📦 Manajemen Barang")
    barang_data = load_data(BARANG_FILE)
    kategori_data = load_data(KATEGORI_FILE)

    nama = st.text_input("Nama Barang")
    kategori = st.selectbox("Kategori", kategori_data)
    harga = st.number_input("Harga", min_value=0)
    stok = st.number_input("Stok", min_value=0)

    if st.button("Simpan Barang"):
        for item in barang_data:
            if item['nama'] == nama and item['kategori'] == kategori:
                item['harga'] = harga
                item['stok'] += stok
                break
        else:
            barang_data.append({"nama": nama, "kategori": kategori, "harga": harga, "stok": stok})
        save_data(BARANG_FILE, barang_data)
        st.success("Barang berhasil ditambahkan/diupdate")

    df = pd.DataFrame(barang_data)
    st.write("### Daftar Barang")
    st.dataframe(df)

def transaksi_page():
    st.subheader("🛒 Transaksi")
    barang_data = load_data(BARANG_FILE)
    transaksi_data = load_data(TRANSAKSI_FILE)
    user = st.session_state.username

    barang_nama = [f"{b['nama']} - {b['kategori']}" for b in barang_data]
    pilihan = st.selectbox("Pilih Barang", barang_nama)
    jumlah = st.number_input("Jumlah", min_value=1, step=1)

    if st.button("Bayar"):
        idx = barang_nama.index(pilihan)
        item = barang_data[idx]
        if item['stok'] < jumlah:
            st.error("Stok tidak mencukupi.")
        else:
            total = jumlah * item['harga']
            item['stok'] -= jumlah
            save_data(BARANG_FILE, barang_data)

            transaksi = {
                "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nama": item['nama'],
                "kategori": item['kategori'],
                "jumlah": jumlah,
                "harga": item['harga'],
                "total": total,
                "kasir": user
            }
            transaksi_data.append(transaksi)
            save_data(TRANSAKSI_FILE, transaksi_data)

            st.success("Transaksi berhasil disimpan.")
            if st.checkbox("Cetak Nota"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="NOTA TRANSAKSI", ln=True, align='C')
                for k, v in transaksi.items():
                    pdf.cell(200, 10, txt=f"{k.capitalize()}: {v}", ln=True)
                pdf_output = io.BytesIO()
                pdf.output(pdf_output)
                st.download_button("Unduh Nota (PDF)", pdf_output.getvalue(), file_name="nota.pdf")

def laporan_page():
    st.subheader("📈 Laporan Keuangan")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)

    if df.empty:
        st.info("Belum ada transaksi.")
        return

    df['tanggal'] = pd.to_datetime(df['tanggal'])
    start = st.date_input("Tanggal Awal", df['tanggal'].min().date())
    end = st.date_input("Tanggal Akhir", df['tanggal'].max().date())

    mask = (df['tanggal'].dt.date >= start) & (df['tanggal'].dt.date <= end)
    df_filtered = df[mask]

    st.write("### Ringkasan Transaksi")
    st.dataframe(df_filtered)

    st.write("### Grafik Total Harian")
    chart = df_filtered.groupby(df_filtered['tanggal'].dt.date)['total'].sum().reset_index()
    fig = px.bar(chart, x='tanggal', y='total', title="Pendapatan Harian")
    st.plotly_chart(fig)

    total = df_filtered['total'].sum()
    st.metric("Total Pendapatan", f"Rp {total:,.0f}")

    to_excel = df_filtered.to_excel(index=False)
    st.download_button("📥 Download Laporan (Excel)", data=to_excel, file_name="laporan_keuangan.xlsx")

# ------------------- App ------------------- #
if "logged_in" not in st.session_state:
    login_user()
else:
    main_menu()
