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

# Setup admin awal

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
                st.success("Login berhasil! Memuat aplikasi...")
                st.stop()  # Ini cukup, karena di main akan rerun dan menu akan tampil
        st.error("Username atau password salah.")

# Dashboard
def halaman_dashboard():
    st.subheader("📊 Dashboard")
    data = load_data(TRANSAKSI_FILE)
    total_transaksi = len(data)
    total_pendapatan = sum(t["total"] for t in data)
    col1, col2 = st.columns(2)
    col1.metric("Jumlah Transaksi", total_transaksi)
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")

# Barang
def halaman_barang():
    st.subheader("📦 Manajemen Barang")
    barang = load_data(BARANG_FILE)

    with st.expander("➕ Tambah Barang"):
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        stok = st.number_input("Stok", 0)
        harga = st.number_input("Harga Satuan", 0)
        harga_modal = st.number_input("Harga Modal", 0)
        if st.button("Simpan"):
            if any(b["nama"] == nama and b["kategori"] == kategori for b in barang):
                st.warning("Barang dengan nama & kategori sama sudah ada.")
            else:
                barang.append({
                    "nama": nama,
                    "kategori": kategori,
                    "stok": stok,
                    "harga": harga,
                    "harga_modal": harga_modal
                })
                save_data(BARANG_FILE, barang)
                st.success("Barang ditambahkan.")

    df = pd.DataFrame(barang)
    st.dataframe(df)

# Transaksi
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
                "harga_modal": b.get("harga_modal", 0),
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

# Riwayat
def halaman_riwayat():
    st.subheader("📜 Riwayat Transaksi")
    data = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(data)
    st.dataframe(df)

# Laporan

def halaman_laporan():
    st.subheader("📈 Laporan Keuangan")
    data = load_data(TRANSAKSI_FILE)
    if not data:
        st.info("Belum ada data.")
        return

    df = pd.DataFrame(data)
    df['waktu'] = pd.to_datetime(df['waktu'])
    df['tanggal'] = df['waktu'].dt.date
    df['bulan'] = df['waktu'].dt.to_period('M')

    st.write("### 📅 Pendapatan Harian")
    harian = df.groupby("tanggal")["total"].sum()
    st.line_chart(harian)

    st.write("### 📆 Pendapatan Bulanan")
    bulanan = df.groupby("bulan")["total"].sum()
    st.bar_chart(bulanan)

    # Ekspor ke Excel
    if st.button("📤 Ekspor Excel"):
        out_df = df[["waktu", "kasir", "total"]]
        out_df.to_excel("laporan_penjualan.xlsx", index=False)
        with open("laporan_penjualan.xlsx", "rb") as f:
            st.download_button("Download Excel", f, "laporan_penjualan.xlsx")

# Statistik

def halaman_statistik():
    st.subheader("📊 Statistik Penjualan")
    data = load_data(TRANSAKSI_FILE)
    if not data:
        st.info("Belum ada data transaksi.")
        return

    df = pd.DataFrame(data)
    df['waktu'] = pd.to_datetime(df['waktu'])
    df['tanggal'] = df['waktu'].dt.date

    # Barang Terlaris
    from collections import Counter
    all_items = []
    for t in data:
        for item in t['items']:
            all_items.append(item['nama'])

    counter = Counter(all_items)
    terlaris_df = pd.DataFrame(counter.items(), columns=["Barang", "Jumlah Terjual"]).sort_values(by="Jumlah Terjual", ascending=False)
    st.write("### 📦 Barang Terlaris")
    st.dataframe(terlaris_df)
    st.bar_chart(terlaris_df.set_index("Barang"))

    # Pendapatan Harian
    st.write("### 💰 Pendapatan Harian")
    pendapatan_harian = df.groupby("tanggal")["total"].sum().reset_index().sort_values(by="total", ascending=False)
    st.dataframe(pendapatan_harian.rename(columns={"total": "Pendapatan"}))
    st.line_chart(pendapatan_harian.set_index("tanggal"))

    # Laba Kotor
    st.write("### 📈 Laba Kotor Harian")
    laba_dict = {}
    for t in data:
        tgl = pd.to_datetime(t["waktu"]).date()
        laba_hari = 0
        for item in t["items"]:
            harga_modal = item.get("harga_modal")
            if harga_modal:
                laba_hari += (item["harga"] - harga_modal) * item["qty"]
        laba_dict[tgl] = laba_dict.get(tgl, 0) + laba_hari

    laba_df = pd.DataFrame(list(laba_dict.items()), columns=["Tanggal", "Laba Kotor"])
    st.dataframe(laba_df.sort_values(by="Tanggal"))
    st.line_chart(laba_df.set_index("Tanggal"))

    # Rata-rata Transaksi per Hari
    st.write("### 🧾 Rata-rata Transaksi per Hari")
    rata_df = df.groupby("tanggal").size().reset_index(name="Jumlah Transaksi")
    rata_rata = rata_df["Jumlah Transaksi"].mean()
    st.metric("Rata-rata Transaksi/Hari", f"{rata_rata:.2f}")

    # Performa Kasir
    st.write("### 🧍 Performa Kasir")
    kasir_df = df.groupby("kasir")["total"].agg(["count", "sum"]).reset_index().rename(columns={"count": "Jumlah Transaksi", "sum": "Total Penjualan"})
    st.dataframe(kasir_df)
    st.bar_chart(kasir_df.set_index("kasir")[["Total Penjualan"]])

# Akun

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
    st.stop()  # Penting agar tidak lanjut ke bawah sebelum login

menu = {
    "Dashboard": halaman_dashboard,
    "Barang": halaman_barang,
    "Transaksi": halaman_transaksi,
    "Riwayat": halaman_riwayat,
    "Laporan": halaman_laporan,
    "Statistik": halaman_statistik
}

if st.session_state["login"]["role"] == "admin":
    menu["Manajemen Akun"] = halaman_akun

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
        "Statistik": "📊",
        "Manajemen Akun": "👥"
    }
    pilihan = st.radio("📌 Menu", [f"{menu_icon[m]} {m}" for m in menu.keys()])

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🔓 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logout berhasil.")
        st.experimental_rerun()

menu_label = pilihan.split(" ", 1)[1]
st.title("Aplikasi Kasir")
menu[menu_label]()
