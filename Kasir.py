# aplikasi_kasir.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import bcrypt
from fpdf import FPDF
import qrcode
from PIL import Image
import io

# Konfigurasi
st.set_page_config(page_title="Aplikasi Kasir", layout="wide")
AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"

# Utilitas
def load_data(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Setup admin awal jika file akun kosong
def setup_admin():
    akun = load_data(AKUN_FILE)
    if not akun:
        st.warning("Setup Admin Pertama Kali")
        with st.form("form_admin"):
            username = st.text_input("Username Admin")
            password = st.text_input("Password Admin", type="password")
            submit = st.form_submit_button("Buat Akun Admin")
            if submit:
                akun.append({
                    "username": username,
                    "password": hash_password(password),
                    "role": "admin"
                })
                save_data(AKUN_FILE, akun)
                st.success("Admin berhasil dibuat! Silakan login.")
                st.stop()

# Login
def login():
    akun = load_data(AKUN_FILE)
    st.title("🔐 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        for a in akun:
            if a["username"] == username and check_password(password, a["password"]):
                st.session_state.login = {"username": username, "role": a["role"]}
                st.success("Login berhasil!")
                st.experimental_rerun()
        st.error("Username atau password salah.")
        st.stop()

# Halaman Dashboard
def halaman_dashboard():
    st.subheader("📊 Dashboard")
    data = load_data(TRANSAKSI_FILE)
    total_transaksi = len(data)
    total_pendapatan = sum(t["total"] for t in data)
    col1, col2 = st.columns(2)
    col1.metric("Jumlah Transaksi", total_transaksi)
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")

# Halaman Barang
def halaman_barang():
    st.subheader("📦 Manajemen Barang")
    barang = load_data(BARANG_FILE)

    with st.expander("➕ Tambah Barang"):
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        stok = st.number_input("Stok", 0)
        harga = st.number_input("Harga Satuan", 0)
        if st.button("Simpan"):
            if any(b["nama"] == nama and b["kategori"] == kategori for b in barang):
                st.warning("Barang dengan nama & kategori sama sudah ada.")
            else:
                barang.append({
                    "nama": nama,
                    "kategori": kategori,
                    "stok": stok,
                    "harga": harga
                })
                save_data(BARANG_FILE, barang)
                st.success("Barang ditambahkan.")

    df = pd.DataFrame(barang)
    st.dataframe(df)

# Halaman Transaksi
def halaman_transaksi():
    st.subheader("🛒 Transaksi")
    barang = load_data(BARANG_FILE)
    transaksi = load_data(TRANSAKSI_FILE)

    keranjang = []
    total = 0

    for b in barang:
        qty = st.number_input(f"{b['nama']} ({b['kategori']}) - Stok: {b['stok']}", 0, b['stok'], key=b['nama'])
        if qty > 0:
            subtotal = b['harga'] * qty
            keranjang.append({
                "nama": b['nama'],
                "kategori": b['kategori'],
                "qty": qty,
                "harga": b['harga'],
                "subtotal": subtotal
            })
            total += subtotal

    if keranjang:
        st.write("### Ringkasan Transaksi")
        df = pd.DataFrame(keranjang)
        st.dataframe(df)
        st.write(f"**Total: Rp {total:,.0f}**")
        if st.button("Simpan Transaksi"):
            for item in keranjang:
                for b in barang:
                    if b["nama"] == item["nama"] and b["kategori"] == item["kategori"]:
                        b["stok"] -= item["qty"]
            transaksi.append({
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "kasir": st.session_state.login["username"],
                "items": keranjang,
                "total": total
            })
            save_data(BARANG_FILE, barang)
            save_data(TRANSAKSI_FILE, transaksi)
            st.success("Transaksi berhasil disimpan.")

# Halaman Riwayat Transaksi
def halaman_riwayat():
    st.subheader("📜 Riwayat Transaksi")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)
    st.dataframe(df)

# Halaman Laporan
def halaman_laporan():
    st.subheader("📈 Laporan Keuangan")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)
    if not df.empty:
        df['waktu'] = pd.to_datetime(df['waktu'])
        df['tanggal'] = df['waktu'].dt.date
        laporan = df.groupby("tanggal")["total"].sum().reset_index()
        st.line_chart(laporan.set_index("tanggal"))

# Halaman Manajemen Akun (admin only)
def halaman_akun():
    st.subheader("👤 Manajemen Akun")
    akun = load_data(AKUN_FILE)
    username = st.text_input("Username Baru")
    password = st.text_input("Password Baru", type="password")
    role = st.selectbox("Role", ["admin", "kasir"])
    if st.button("Tambah Akun"):
        if any(a["username"] == username for a in akun):
            st.warning("Username sudah digunakan.")
        else:
            akun.append({
                "username": username,
                "password": hash_password(password),
                "role": role
            })
            save_data(AKUN_FILE, akun)
            st.success("Akun berhasil ditambahkan.")

    df = pd.DataFrame(akun).drop(columns=["password"])
    st.dataframe(df)

# ========== MAIN ==========
setup_admin()

if "login" not in st.session_state:
    login()

# Menu dengan ikon
menu = {
    "Dashboard": halaman_dashboard,
    "Barang": halaman_barang,
    "Transaksi": halaman_transaksi,
    "Riwayat": halaman_riwayat,
    "Laporan": halaman_laporan,
}
if st.session_state.login["role"] == "admin":
    menu["Manajemen Akun"] = halaman_akun

# ===== Sidebar Fancy =====
with st.sidebar:
    st.markdown("""
        <style>
        .sidebar-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .user-badge {
            display: inline-block;
            background-color: #22c55e;
            color: white;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">📋 <span>Kasir App</span></div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom: 12px;">
            👤 Login sebagai: <span class="user-badge">{st.session_state.login['username']}</span><br>
            ({st.session_state.login['role']})
        </div>
    """, unsafe_allow_html=True)

    menu_icon = {
        "Dashboard": "🏠",
        "Barang": "📦",
        "Transaksi": "🛒",
        "Riwayat": "📜",
        "Laporan": "📈",
        "Manajemen Akun": "👥"
    }
    pilihan = st.radio("📌 Menu", [f"{menu_icon[m]} {m}" for m in menu.keys()])

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🔓 Logout"):
        del st.session_state.login
        st.experimental_rerun()

# Jalankan halaman terpilih
menu_label = pilihan.split(" ", 1)[1]
st.title("Aplikasi Kasir")
menu[menu_label]()
