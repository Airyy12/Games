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
BARANG_HAPUS_FILE = "barang_dihapus.json"

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
                st.success("Login berhasil!")
                st.experimental_rerun()
        st.error("Username atau password salah.")
        st.stop()

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

    st.write("### 🗑️ Hapus Barang")
    if barang:
        index = st.selectbox("Pilih Barang", range(len(barang)), format_func=lambda i: f"{barang[i]['nama']} ({barang[i]['kategori']})")
        keterangan = st.text_input("Alasan Penghapusan")
        tanggal = st.date_input("Tanggal Penghapusan", datetime.now())
        if st.button("Hapus Barang"):
            barang_dihapus = load_data(BARANG_HAPUS_FILE)
            data_dihapus = barang.pop(index)
            barang_dihapus.append({
                **data_dihapus,
                "keterangan": keterangan,
                "tanggal_dihapus": tanggal.strftime("%Y-%m-%d")
            })
            save_data(BARANG_FILE, barang)
            save_data(BARANG_HAPUS_FILE, barang_dihapus)
            st.success("Barang berhasil dihapus.")
# Transaksi
def halaman_transaksi():
    st.subheader("🛒 Transaksi")
    barang = load_data(BARANG_FILE)
    transaksi = load_data(TRANSAKSI_FILE)
    kategori_terpilih = st.selectbox("Pilih Kategori", sorted(set(b['kategori'] for b in barang)))

    nama_barang_list = [b['nama'] for b in barang if b['kategori'] == kategori_terpilih]
    nama_barang = st.selectbox("Pilih Barang", nama_barang_list)

    b_dipilih = next((b for b in barang if b['nama'] == nama_barang and b['kategori'] == kategori_terpilih), None)
    if not b_dipilih:
        st.warning("Barang tidak ditemukan.")
        return

    qty = st.number_input(f"Jumlah ({b_dipilih['stok']} tersedia)", 0, b_dipilih['stok'])

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    if st.button("➕ Tambah ke Keranjang") and qty > 0:
        st.session_state.keranjang.append({
            "nama": b_dipilih['nama'],
            "kategori": b_dipilih['kategori'],
            "qty": qty,
            "harga": b_dipilih['harga'],
            "harga_modal": b_dipilih.get("harga_modal", 0),
            "subtotal": b_dipilih['harga'] * qty
        })

    if st.session_state.keranjang:
        st.write("### 🧺 Keranjang Belanja")
        df = pd.DataFrame(st.session_state.keranjang)
        st.dataframe(df)
        total = sum(item['subtotal'] for item in st.session_state.keranjang)
        st.write(f"**Total: Rp {total:,.0f}**")

        hapus_idx = st.number_input("Hapus item di keranjang (berdasarkan indeks)", 0, len(st.session_state.keranjang)-1, step=1)
        if st.button("❌ Hapus Item"):
            st.session_state.keranjang.pop(hapus_idx)

        if st.button("💾 Simpan Transaksi"):
            for item in st.session_state.keranjang:
                for b in barang:
                    if b["nama"] == item["nama"] and b["kategori"] == item["kategori"]:
                        b["stok"] -= item["qty"]
            transaksi.append({
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "kasir": st.session_state.login["username"],
                "items": st.session_state.keranjang,
                "total": total
            })
            save_data(BARANG_FILE, barang)
            save_data(TRANSAKSI_FILE, transaksi)
            st.session_state.keranjang = []
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
    st.stop()

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

