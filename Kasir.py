# kasir.py
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
from fpdf import FPDF
import qrcode
import io
import base64

# === CONFIG ===
st.set_page_config(page_title="Aplikasi Kasir", layout="wide")
DB_FILE = "kasir.db"
STOK_MINIMUM = 5  # Notifikasi jika stok <= 5

# === DB UTILS ===
def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

def init_db():
    with connect_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS akun (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        );
        CREATE TABLE IF NOT EXISTS barang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            kategori TEXT,
            harga_modal INTEGER,
            harga_jual INTEGER,
            stok INTEGER DEFAULT 0,
            terjual INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT,
            user TEXT,
            barang_id INTEGER,
            jumlah INTEGER,
            total INTEGER,
            keuntungan INTEGER,
            FOREIGN KEY (barang_id) REFERENCES barang(id)
        );
        """)
init_db()

# === AUTH ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password, role):
    with connect_db() as conn:
        cur = conn.execute(
            "SELECT * FROM akun WHERE username=? AND password=? AND role=?",
            (username, hash_password(password), role))
        return cur.fetchone()

def create_user(username, password, role):
    try:
        with connect_db() as conn:
            conn.execute(
                "INSERT INTO akun (username, password, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role))
            return True
    except sqlite3.IntegrityError:
        return False

# === PDF STRUK ===
def buat_struk_pdf(transaksi, total, bayar, kembalian):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="TOKO WAWAN", ln=True, align="C")
    pdf.cell(200, 10, txt="Jl. Contoh No.1, Telp 0812-XXXX-XXXX", ln=True, align="C")
    pdf.cell(0, 10, txt="-"*50, ln=True)

    for t in transaksi:
        pdf.cell(0, 10, txt=f"{t['nama']} x{t['jumlah']} @Rp{t['harga_jual']:,}", ln=True)
        pdf.cell(0, 10, txt=f"  Rp{t['subtotal']:,}", ln=True)

    pdf.cell(0, 10, txt="-"*50, ln=True)
    pdf.cell(0, 10, txt=f"Subtotal: Rp{total:,}", ln=True)
    pdf.cell(0, 10, txt=f"Bayar:    Rp{bayar:,}", ln=True)
    pdf.cell(0, 10, txt=f"Kembali:  Rp{kembalian:,}", ln=True)
    pdf.cell(0, 10, txt="-"*50, ln=True)
    pdf.cell(0, 10, txt="Terima kasih atas kunjungan Anda!", ln=True, align="C")

    # Tambahkan QR Code
    qr_data = f"TOKO WAWAN | Total: Rp{total:,}"
    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    pdf.image(buf, x=80, y=pdf.get_y(), w=50)

    # Export to BytesIO
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# === LOGIN ===
def tampilkan_login():
    st.title("🔒 Login Kasir")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["admin", "kasir"], horizontal=True)
        if st.button("Masuk"):
            if check_login(username, password, role):
                st.session_state.login = True
                st.session_state.user = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Login gagal! Periksa username/password/role.")

    with tab2:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Role Baru", ["admin", "kasir"], horizontal=True)
        if st.button("Daftar"):
            if create_user(new_user, new_pass, new_role):
                st.success("Akun berhasil dibuat!")
            else:
                st.warning("Username sudah terdaftar.")

if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

# === SIDEBAR ===
st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("🔓 Logout"):
    st.session_state.clear()
    st.rerun()

# === MENU ===
menu = ["📦 Input Barang", "🛒 Kasir", "📋 Stok", "🧾 Riwayat", "📊 Dashboard", "📤 Ekspor"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(menu)

# === 📦 INPUT BARANG ===
with tab1:
    st.header("📦 Input Barang")
    if st.session_state.role != "admin":
        st.warning("Hanya admin yang bisa menambah barang.")
    else:
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        modal = st.number_input("Harga Modal", min_value=0)
        jual = st.number_input("Harga Jual", min_value=0)
        stok = st.number_input("Stok Awal", min_value=0, step=1)
        if st.button("💾 Simpan Barang"):
            with connect_db() as conn:
                conn.execute("INSERT INTO barang (nama, kategori, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?, ?)",
                             (nama, kategori, modal, jual, stok))
            st.success(f"Barang '{nama}' disimpan.")

        # Tampilkan data barang
        df_barang = pd.read_sql("SELECT * FROM barang", connect_db())
        st.dataframe(df_barang)

# === 🛒 KASIR ===
with tab2:
    st.header("🛒 Transaksi Kasir")
    df_barang = pd.read_sql("SELECT * FROM barang WHERE stok > 0", connect_db())

    if df_barang.empty:
        st.warning("Stok barang kosong.")
    else:
        if "keranjang" not in st.session_state:
            st.session_state.keranjang = []

        cari_barang = st.text_input("🔍 Cari Barang")
        df_filtered = df_barang[df_barang["nama"].str.contains(cari_barang, case=False)] if cari_barang else df_barang

        barang_pilih = st.selectbox("Pilih Barang", df_filtered["nama"])
        b_data = df_filtered[df_filtered["nama"] == barang_pilih].iloc[0]
        jumlah_beli = st.number_input("Jumlah", min_value=1, max_value=b_data["stok"], step=1)
        if st.button("🛒 Tambah ke Keranjang"):
            st.session_state.keranjang.append({
                "id": b_data["id"],
                "nama": barang_pilih,
                "jumlah": jumlah_beli,
                "harga_jual": b_data["harga_jual"],
                "subtotal": jumlah_beli * b_data["harga_jual"]
            })
            st.success(f"{jumlah_beli} {barang_pilih} ditambahkan ke keranjang.")

        # Tampilkan keranjang
        if st.session_state.keranjang:
            df_cart = pd.DataFrame(st.session_state.keranjang)
            st.table(df_cart)
            total = df_cart["subtotal"].sum()
            st.markdown(f"### 💵 Total: Rp{total:,}")
            bayar = st.number_input("💵 Uang Diterima", min_value=0, step=1000)

            if st.button("✅ Proses Transaksi"):
                if bayar < total:
                    st.error("Uang tidak cukup.")
                else:
                    kembali = bayar - total
                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with connect_db() as conn:
                        for item in st.session_state.keranjang:
                            conn.execute("""
                                UPDATE barang SET stok = stok - ?, terjual = terjual + ? WHERE id = ?
                            """, (item["jumlah"], item["jumlah"], item["id"]))
                            keuntungan = (item["harga_jual"] - df_barang[df_barang["id"] == item["id"]]["harga_modal"].values[0]) * item["jumlah"]
                            conn.execute("""
                                INSERT INTO transaksi (waktu, user, barang_id, jumlah, total, keuntungan)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (waktu, st.session_state.user, item["id"], item["jumlah"], item["subtotal"], keuntungan))

                    st.success("Transaksi berhasil.")
                    pdf_file = buat_struk_pdf(st.session_state.keranjang, total, bayar, kembali)
                    st.download_button("🖨️ Download Struk (PDF)", data=pdf_file, file_name="struk.pdf")
                    st.session_state.keranjang.clear()

# === 📋 STOK ===
with tab3:
    st.header("📋 Status Stok Barang")
    df_barang = pd.read_sql("SELECT * FROM barang", connect_db())
    st.dataframe(df_barang)

    if st.session_state.role == "admin":
        for _, row in df_barang.iterrows():
            if row["stok"] <= STOK_MINIMUM:
                st.warning(f"⚠️ Stok rendah: {row['nama']} hanya {row['stok']} tersisa!")

# === 🧾 RIWAYAT ===
with tab4:
    st.header("🧾 Riwayat Transaksi")
    df_trx = pd.read_sql("""
        SELECT t.id, t.waktu, t.user, b.nama, t.jumlah, t.total, t.keuntungan
        FROM transaksi t
        JOIN barang b ON t.barang_id = b.id
    """, connect_db())
    st.dataframe(df_trx)

# === 📊 DASHBOARD ===
with tab5:
    st.header("📊 Dashboard")
    df_trx = pd.read_sql("SELECT * FROM transaksi", connect_db())
    if not df_trx.empty:
        fig = px.bar(df_trx, x="waktu", y="total", color="user", title="Total Penjualan")
        st.plotly_chart(fig, use_container_width=True)

# === 📤 EKSPOR ===
with tab6:
    st.header("📤 Ekspor Data")
    col1, col2 = st.columns(2)
    with col1:
        df_barang = pd.read_sql("SELECT * FROM barang", connect_db())
        st.download_button("⬇️ Ekspor Barang (CSV)", df_barang.to_csv(index=False), file_name="barang.csv")
    with col2:
        df_trx = pd.read_sql("SELECT * FROM transaksi", connect_db())
        st.download_button("⬇️ Ekspor Transaksi (CSV)", df_trx.to_csv(index=False), file_name="transaksi.csv")
