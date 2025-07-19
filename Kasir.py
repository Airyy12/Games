import streamlit as st
import pandas as pd
import json
import os
import bcrypt
from datetime import datetime
import plotly.express as px
import io

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"
KATEGORI_FILE = "kategori.json"

# ---------- Fungsi Load & Save ---------- #
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Buat Admin Default ---------- #
def buat_admin_default():
    if not os.path.exists(AKUN_FILE):
        admin_default = [{
            "username": "admin",
            "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
            "role": "admin"
        }]
        save_data(AKUN_FILE, admin_default)
    else:
        akun = load_data(AKUN_FILE)
        if not any(user['role'] == 'admin' for user in akun):
            akun.append({
                "username": "admin",
                "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
                "role": "admin"
            })
            save_data(AKUN_FILE, akun)

buat_admin_default()

# ---------- Login ---------- #
def login():
    akun = load_data(AKUN_FILE)
    st.title("🔐 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        for user in akun:
            if user["username"] == username and bcrypt.checkpw(password.encode(), user["password"].encode()):
                st.session_state.login = True
                st.session_state.username = user["username"]
                st.session_state.role = user.get("role", "kasir")
                st.experimental_rerun()
        st.error("Username atau password salah.")

# ---------- Tambah User oleh Admin ---------- #
def halaman_manajemen_user():
    st.subheader("👤 Tambah User Baru (Admin Only)")
    akun = load_data(AKUN_FILE)
    new_username = st.text_input("Username Baru")
    new_password = st.text_input("Password Baru", type="password")
    confirm_password = st.text_input("Konfirmasi Password", type="password")
    role = st.selectbox("Role", ["kasir", "admin"])

    if st.button("Tambah User"):
        if new_password != confirm_password:
            st.warning("Password tidak cocok.")
        elif any(u["username"] == new_username for u in akun):
            st.warning("Username sudah digunakan.")
        else:
            hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            akun.append({"username": new_username, "password": hashed_pw, "role": role})
            save_data(AKUN_FILE, akun)
            st.success(f"User '{new_username}' berhasil dibuat sebagai {role}.")

# ---------- Manajemen Barang ---------- #
def halaman_barang():
    st.header("📦 Manajemen Barang")
    barang = load_data(BARANG_FILE)
    kategori = load_data(KATEGORI_FILE)

    if not kategori:
        st.warning("Kategori masih kosong. Tambahkan kategori terlebih dahulu.")
        return

    nama = st.text_input("Nama Barang")
    kategori_input = st.selectbox("Kategori", kategori)
    harga = st.number_input("Harga", min_value=0)
    stok = st.number_input("Stok", min_value=0)

    if st.button("Tambah Barang"):
        if any(b["nama"] == nama and b["kategori"] == kategori_input for b in barang):
            st.warning("Barang dengan nama dan kategori yang sama sudah ada.")
        else:
            barang.append({"nama": nama, "kategori": kategori_input, "harga": harga, "stok": stok})
            save_data(BARANG_FILE, barang)
            st.success("Barang berhasil ditambahkan.")

    st.write(pd.DataFrame(barang))

# ---------- Manajemen Kategori ---------- #
def halaman_kategori():
    st.header("🏷️ Manajemen Kategori")
    kategori = load_data(KATEGORI_FILE)
    new_kategori = st.text_input("Tambah Kategori Baru")
    if st.button("Tambah Kategori"):
        if new_kategori in kategori:
            st.warning("Kategori sudah ada.")
        else:
            kategori.append(new_kategori)
            save_data(KATEGORI_FILE, kategori)
            st.success("Kategori ditambahkan.")
    st.write(pd.DataFrame(kategori, columns=["Kategori"]))

# ---------- Transaksi ---------- #
def halaman_transaksi():
    st.header("💰 Transaksi Penjualan")
    barang = load_data(BARANG_FILE)
    transaksi = load_data(TRANSAKSI_FILE)

    if not barang:
        st.warning("Data barang kosong.")
        return

    keranjang = []
    for b in barang:
        qty = st.number_input(f"{b['nama']} ({b['stok']} stok) - Rp{b['harga']}", min_value=0, max_value=b['stok'], key=b['nama'])
        if qty > 0:
            keranjang.append({"nama": b["nama"], "harga": b["harga"], "qty": qty})

    diskon = st.number_input("Diskon (%)", min_value=0, max_value=100, value=0)
    if keranjang and st.button("Bayar"):
        total = sum(item['harga'] * item['qty'] for item in keranjang)
        total_diskon = total * (diskon / 100)
        total_bayar = total - total_diskon
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in keranjang:
            for b in barang:
                if b['nama'] == item['nama']:
                    b['stok'] -= item['qty']

        transaksi.append({
            "waktu": waktu,
            "kasir": st.session_state.username,
            "item": keranjang,
            "total": total,
            "diskon": diskon,
            "total_bayar": total_bayar
        })

        save_data(BARANG_FILE, barang)
        save_data(TRANSAKSI_FILE, transaksi)
        st.success(f"Transaksi berhasil. Total bayar: Rp{total_bayar:,}")

# ---------- Laporan Keuangan ---------- #
def halaman_laporan():
    st.header("📊 Laporan Keuangan")
    transaksi = load_data(TRANSAKSI_FILE)
    if not transaksi:
        st.warning("Belum ada transaksi.")
        return

    df = pd.DataFrame(transaksi)
    df['waktu'] = pd.to_datetime(df['waktu'])
    df['tanggal'] = df['waktu'].dt.date
    df['total_bayar'] = df['total_bayar'].astype(float)

    st.line_chart(df.groupby("tanggal")["total_bayar"].sum())
    st.write("Total Penjualan:", f"Rp{df['total_bayar'].sum():,.0f}")

    if st.button("📤 Export Excel"):
        excel = io.BytesIO()
        df.to_excel(excel, index=False, sheet_name="Laporan")
        st.download_button("Download", excel.getvalue(), file_name="laporan.xlsx")

# ---------- Main App ---------- #
def main():
    if "login" not in st.session_state:
        st.session_state.login = False

    if not st.session_state.login:
        login()
        return

    st.sidebar.title(f"👋 Selamat Datang, {st.session_state.username}")
    menu = st.sidebar.selectbox("Menu", [
        "Transaksi", "Barang", "Kategori", "Laporan Keuangan"
    ])

    if menu == "Transaksi":
        halaman_transaksi()
    elif menu == "Barang":
        halaman_barang()
    elif menu == "Kategori":
        halaman_kategori()
    elif menu == "Laporan Keuangan":
        halaman_laporan()

    if st.session_state.role == "admin":
        st.sidebar.markdown("---")
        if st.sidebar.button("🧑‍💼 Tambah User Baru"):
            halaman_manajemen_user()

    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
