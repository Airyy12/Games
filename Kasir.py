import streamlit as st
import pandas as pd
import os
import json
import bcrypt
import qrcode
from PIL import Image
from datetime import datetime
from fpdf import FPDF
import plotly.express as px

# ------------------- Konstanta file -------------------
AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"
KATEGORI_FILE = "kategori.json"

# ------------------- Fungsi Utilitas -------------------
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

def buat_nota_pdf(transaksi):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Nota Transaksi", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Tanggal: {transaksi['tanggal']}", ln=True)
    pdf.cell(0, 10, f"Kasir: {transaksi['user']}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Nama", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(40, 10, "Harga", 1)
    pdf.cell(40, 10, "Total", 1, ln=True)

    pdf.set_font("Arial", "", 12)
    for item in transaksi['items']:
        pdf.cell(60, 10, item['nama'], 1)
        pdf.cell(30, 10, str(item['qty']), 1)
        pdf.cell(40, 10, f"{item['harga']:,}", 1)
        pdf.cell(40, 10, f"{item['total']:,}", 1, ln=True)

    pdf.cell(0, 10, f"Total: Rp {transaksi['total']:,}", ln=True)

    filename = f"nota_{transaksi['id']}.pdf"
    pdf.output(filename)

    return filename

def generate_qr(transaksi_id):
    img = qrcode.make(f"ID Transaksi: {transaksi_id}")
    path = f"qr_{transaksi_id}.png"
    img.save(path)
    return path

# ------------------- Setup Admin Pertama Kali -------------------
akun = load_data(AKUN_FILE)
if len(akun) == 0:
    st.title("🛠️ Setup Admin Pertama Kali")
    username = st.text_input("Username Admin")
    password = st.text_input("Password Admin", type="password")
    if st.button("Buat Admin"):
        hashed_pw = hash_password(password)
        akun.append({"username": username, "password": hashed_pw, "role": "admin"})
        save_data(AKUN_FILE, akun)
        st.success("Admin berhasil dibuat. Silakan login.")
        st.stop()

# ------------------- Login -------------------
if "login" not in st.session_state:
    st.session_state.login = None

if not st.session_state.login:
    st.title("🔐 Login Kasir")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        akun = load_data(AKUN_FILE)
        for a in akun:
            if a["username"] == username and check_password(password, a["password"]):
                st.session_state.login = {"username": username, "role": a["role"]}
                st.success("Login berhasil!")
                st.rerun()
        st.error("Username atau password salah.")
    st.stop()

# ------------------- Layout Setelah Login -------------------
user = st.session_state.login["username"]
role = st.session_state.login["role"]

st.sidebar.success(f"Login sebagai: {user} ({role})")
menu = st.sidebar.radio("Menu", [
    "Transaksi", 
    "Riwayat", 
    "Laporan",
    "Stok Barang", 
    "Kategori",
    "Registrasi User", 
    "Logout"
])

# ------------------- Logout -------------------
if menu == "Logout":
    st.session_state.login = None
    st.experimental_rerun()

# ------------------- Registrasi User (Admin Only) -------------------
if menu == "Registrasi User":
    if role != "admin":
        st.warning("Hanya admin yang dapat mengakses halaman ini.")
        st.stop()

    st.title("➕ Registrasi Pengguna")
    new_user = st.text_input("Username Baru")
    new_pw = st.text_input("Password Baru", type="password")
    new_role = st.selectbox("Role", ["kasir", "admin"])
    if st.button("Daftarkan"):
        akun = load_data(AKUN_FILE)
        if any(u["username"] == new_user for u in akun):
            st.error("Username sudah ada.")
        else:
            akun.append({"username": new_user, "password": hash_password(new_pw), "role": new_role})
            save_data(AKUN_FILE, akun)
            st.success("User berhasil dibuat.")

# ------------------- Kategori -------------------
if menu == "Kategori":
    st.title("📁 Manajemen Kategori")
    kategori = load_data(KATEGORI_FILE)

    new_cat = st.text_input("Nama Kategori Baru")
    if st.button("Tambah Kategori"):
        if new_cat and new_cat not in kategori:
            kategori.append(new_cat)
            save_data(KATEGORI_FILE, kategori)
            st.success("Kategori ditambahkan.")

    if kategori:
        st.write("Daftar Kategori:")
        for i, k in enumerate(kategori):
            col1, col2 = st.columns([0.9, 0.1])
            col1.write(k)
            if col2.button("❌", key=f"del_kat_{i}"):
                kategori.remove(k)
                save_data(KATEGORI_FILE, kategori)
                st.experimental_rerun()

# ------------------- Stok Barang -------------------
if menu == "Stok Barang":
    st.title("📦 Manajemen Barang")
    barang = load_data(BARANG_FILE)
    kategori = load_data(KATEGORI_FILE)

    nama = st.text_input("Nama Barang")
    kat = st.selectbox("Kategori", kategori)
    harga = st.number_input("Harga", 0)
    stok = st.number_input("Stok", 0)
    if st.button("Tambah Barang"):
        if nama and not any(b["nama"] == nama and b["kategori"] == kat for b in barang):
            barang.append({"nama": nama, "kategori": kat, "harga": harga, "stok": stok})
            save_data(BARANG_FILE, barang)
            st.success("Barang ditambahkan.")
        else:
            st.warning("Barang sudah ada.")

    if barang:
        df = pd.DataFrame(barang)
        st.dataframe(df)

# ------------------- Transaksi -------------------
if menu == "Transaksi":
    st.title("🛒 Transaksi")
    barang = load_data(BARANG_FILE)
    transaksi = load_data(TRANSAKSI_FILE)

    keranjang = []

    for b in barang:
        qty = st.number_input(f"{b['nama']} (stok: {b['stok']})", 0, b['stok'], key=b['nama'])
        if qty > 0:
            total = qty * b['harga']
            keranjang.append({"nama": b['nama'], "qty": qty, "harga": b['harga'], "total": total})

    if keranjang and st.button("Simpan Transaksi"):
        total = sum(item['total'] for item in keranjang)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tid = f"TRX{len(transaksi)+1:04}"
        trx = {"id": tid, "tanggal": now, "user": user, "items": keranjang, "total": total}
        transaksi.append(trx)
        save_data(TRANSAKSI_FILE, transaksi)

        # Kurangi stok
        for item in keranjang:
            for b in barang:
                if b["nama"] == item["nama"]:
                    b["stok"] -= item["qty"]
        save_data(BARANG_FILE, barang)

        pdf_path = buat_nota_pdf(trx)
        qr_path = generate_qr(tid)
        st.success("Transaksi berhasil!")
        st.download_button("📥 Unduh Nota PDF", open(pdf_path, "rb"), file_name=pdf_path)
        st.image(qr_path, caption="QR Code Transaksi")

# ------------------- Riwayat -------------------
if menu == "Riwayat":
    st.title("📜 Riwayat Transaksi")
    transaksi = load_data(TRANSAKSI_FILE)

    df = pd.DataFrame(transaksi)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        df["total"] = df["total"].astype(int)
        st.dataframe(df[["id", "tanggal", "user", "total"]])

# ------------------- Laporan -------------------
if menu == "Laporan":
    st.title("📊 Laporan Keuangan")
    transaksi = load_data(TRANSAKSI_FILE)
    df = pd.DataFrame(transaksi)

    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        df["total"] = df["total"].astype(int)
        df["hari"] = df["tanggal"].dt.date

        st.subheader("Pendapatan per Hari")
        daily = df.groupby("hari")["total"].sum().reset_index()
        fig = px.bar(daily, x="hari", y="total", labels={"hari": "Tanggal", "total": "Pendapatan"})
        st.plotly_chart(fig)

        st.write("Total Pendapatan:", f"Rp {df['total'].sum():,}")
