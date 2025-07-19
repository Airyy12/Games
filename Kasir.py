# aplikasi_kasir.py

import streamlit as st
import pandas as pd
import json
import os
import bcrypt
from datetime import datetime
from fpdf import FPDF
import qrcode
from PIL import Image

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"

# ---------------- FUNGSI UTILITAS ---------------- #

def load_data(file, default=[]):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def login(username, password):
    akun = load_data(AKUN_FILE)
    for user in akun:
        if user['username'] == username and check_password(password, user['password']):
            return user
    return None

# ---------------- HALAMAN LOGIN ---------------- #

if "login_user" not in st.session_state:
    st.session_state.login_user = None

if st.session_state.login_user is None:
    st.title("🔐 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.login_user = user
            st.rerun()
        else:
            st.error("Username atau password salah.")
    st.stop()

# ---------------- MENU UTAMA ---------------- #

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Barang", "Transaksi", "Histori Transaksi", "Laporan Keuangan"] + (["Registrasi User"] if st.session_state.login_user['role'] == "admin" else []) + ["Logout"])

st.sidebar.markdown(f"**Login sebagai:** `{st.session_state.login_user['username']}` ({st.session_state.login_user['role']})")

# ---------------- LOGOUT ---------------- #

if menu == "Logout":
    st.session_state.login_user = None
    st.rerun()

# ---------------- DASHBOARD ---------------- #

elif menu == "Dashboard":
    st.title("📊 Dashboard Ringkasan")
    transaksi = load_data(TRANSAKSI_FILE)
    total = sum(t['total'] for t in transaksi)
    st.metric("Total Penjualan", f"Rp {total:,.0f}")
    st.metric("Total Transaksi", len(transaksi))

# ---------------- BARANG ---------------- #

elif menu == "Barang":
    st.title("📦 Manajemen Barang")
    data = load_data(BARANG_FILE)

    with st.form("form_barang"):
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        harga = st.number_input("Harga", 0)
        stok = st.number_input("Stok", 0)
        submitted = st.form_submit_button("Tambah / Update Barang")
        if submitted:
            if not nama or not kategori:
                st.warning("Nama dan kategori wajib diisi.")
            else:
                found = False
                for item in data:
                    if item['nama'].lower() == nama.lower() and item['kategori'].lower() == kategori.lower():
                        item['harga'] = harga
                        item['stok'] += stok
                        found = True
                        break
                if not found:
                    data.append({"nama": nama, "kategori": kategori, "harga": harga, "stok": stok})
                save_data(BARANG_FILE, data)
                st.success("Barang ditambahkan atau diperbarui.")
                st.rerun()

    st.subheader("Daftar Barang")
    df = pd.DataFrame(data)
    st.dataframe(df)

# ---------------- TRANSAKSI ---------------- #

elif menu == "Transaksi":
    st.title("🛒 Transaksi")
    data_barang = load_data(BARANG_FILE)
    transaksi = []
    total = 0

    for i in range(5):
        col1, col2 = st.columns([3, 1])
        nama = col1.selectbox(f"Barang #{i+1}", [""] + [b['nama'] for b in data_barang], key=f"barang_{i}")
        qty = col2.number_input("Jumlah", 0, key=f"qty_{i}")
        if nama:
            item = next((b for b in data_barang if b['nama'] == nama), None)
            if item:
                subtotal = qty * item['harga']
                total += subtotal
                transaksi.append({
                    "nama": item['nama'],
                    "qty": qty,
                    "harga": item['harga'],
                    "subtotal": subtotal
                })

    st.write("Total: **Rp {:,.0f}**".format(total))
    if st.button("Simpan Transaksi"):
        if not transaksi:
            st.warning("Tidak ada item dipilih.")
        else:
            for t in transaksi:
                for b in data_barang:
                    if b['nama'] == t['nama']:
                        if b['stok'] < t['qty']:
                            st.error(f"Stok tidak cukup untuk {b['nama']}")
                            st.stop()
                        b['stok'] -= t['qty']
            save_data(BARANG_FILE, data_barang)
            transaksi_data = load_data(TRANSAKSI_FILE)
            transaksi_data.append({
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": st.session_state.login_user['username'],
                "item": transaksi,
                "total": total
            })
            save_data(TRANSAKSI_FILE, transaksi_data)
            st.success("Transaksi berhasil disimpan.")

# ---------------- HISTORI ---------------- #

elif menu == "Histori Transaksi":
    st.title("📜 Riwayat Transaksi")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)
    df["waktu"] = pd.to_datetime(df["waktu"])
    df["tanggal"] = df["waktu"].dt.date

    col1, col2 = st.columns(2)
    tanggal = col1.date_input("Filter Tanggal", value=None)
    pengguna = col2.text_input("Filter User")

    if tanggal:
        df = df[df["tanggal"] == pd.to_datetime(tanggal)]
    if pengguna:
        df = df[df["user"].str.contains(pengguna, case=False)]

    for _, row in df.iterrows():
        st.write(f"🕒 {row['waktu']} | 👤 {row['user']} | 💰 Rp {row['total']:,.0f}")
        for item in row['item']:
            st.write(f"- {item['nama']} x {item['qty']} = Rp {item['subtotal']:,.0f}")

# ---------------- LAPORAN ---------------- #

elif menu == "Laporan Keuangan":
    st.title("📈 Laporan Keuangan")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)
    df["waktu"] = pd.to_datetime(df["waktu"])
    df["tanggal"] = df["waktu"].dt.date
    laporan = df.groupby("tanggal")["total"].sum().reset_index()
    st.bar_chart(laporan.set_index("tanggal"))

# ---------------- REGISTRASI ---------------- #

elif menu == "Registrasi User":
    if st.session_state.login_user['role'] != "admin":
        st.warning("Hanya admin yang bisa akses fitur ini.")
        st.stop()

    st.title("🧑‍💼 Registrasi Pengguna Baru")
    username = st.text_input("Username baru")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["admin", "kasir"])
    akun = load_data(AKUN_FILE)

    if st.button("Registrasi"):
        if any(u['username'] == username for u in akun):
            st.error("Username sudah digunakan.")
        else:
            akun.append({
                "username": username,
                "password": hash_password(password),
                "role": role
            })
            save_data(AKUN_FILE, akun)
            st.success(f"User {username} berhasil didaftarkan.")
