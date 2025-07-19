# 📌 aplikasi_kasir.py
import streamlit as st
import pandas as pd
import json
import os
import shutil
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import io
import hashlib
import bcrypt
import sqlite3
from stqdm import stqdm
import warnings
from PIL import Image
import cv2  # Untuk barcode scanner (opsional)
import numpy as np

# 🔒 Konfigurasi Keamanan
warnings.filterwarnings('ignore')
st.set_page_config(
    page_title="Toko Wawan - Aplikasi Kasir", 
    page_icon="🛒", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 📂 File & Database
AKUN_DB = "database/akun.db"
BARANG_DB = "database/barang.db"
TRANSAKSI_DB = "database/transaksi.db"
BACKUP_DIR = "backup/"

# 🔄 Inisialisasi Database
def init_db():
    os.makedirs("database", exist_ok=True)
    
    # Database Akun
    conn = sqlite3.connect(AKUN_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 role TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    
    # Database Barang
    conn = sqlite3.connect(BARANG_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nama TEXT,
                 kategori TEXT,
                 harga_modal REAL,
                 harga_jual REAL,
                 stok INTEGER,
                 barcode TEXT UNIQUE,
                 min_stok INTEGER DEFAULT 3,
                 terjual INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()
    
    # Database Transaksi
    conn = sqlite3.connect(TRANSAKSI_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 waktu TIMESTAMP,
                 items TEXT,  # JSON format
                 subtotal REAL,
                 diskon REAL,
                 pajak REAL,
                 total REAL,
                 pembayaran REAL,
                 kembalian REAL,
                 user TEXT)''')
    conn.commit()
    conn.close()

# 🔐 Fungsi Keamanan
def hash_password(password):
    """Enkripsi password dengan bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(input_password, hashed_password):
    """Verifikasi password"""
    return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 🔄 Backup Otomatis
def auto_backup():
    today = datetime.now().strftime("%Y%m%d")
    backup_file = f"{BACKUP_DIR}backup_{today}.db"
    
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    if not os.path.exists(backup_file):
        for db_file in [AKUN_DB, BARANG_DB, TRANSAKSI_DB]:
            shutil.copy2(db_file, backup_file)
        st.toast("✅ Backup otomatis berhasil dibuat", icon="💾")

# ==============================================
# 🖥️ TAMPILAN APLIKASI
# ==============================================

# 🔐 Modul Login
def login_module():
    st.title("🔑 Login Sistem Kasir")
    tab1, tab2 = st.tabs(["Login", "Daftar Akun (Admin)"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["admin", "kasir"], horizontal=True)
        
        if st.button("Masuk", type="primary"):
            conn = sqlite3.connect(AKUN_DB)
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username=? AND role=?", (username, role))
            result = c.fetchone()
            conn.close()
            
            if result and verify_password(password, result[0]):
                st.session_state.user = username
                st.session_state.role = role
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Username/password salah atau role tidak sesuai!")
    
    with tab2:
        if 'logged_in' in st.session_state and st.session_state.role == 'admin':
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", type="password")
            new_role = st.selectbox("Role", ["admin", "kasir"])
            
            if st.button("Buat Akun"):
                if not new_user or not new_pass:
                    st.warning("Username dan password wajib diisi!")
                else:
                    try:
                        conn = sqlite3.connect(AKUN_DB)
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                 (new_user, hash_password(new_pass), new_role))
                        conn.commit()
                        conn.close()
                        st.success(f"Akun {new_role} untuk {new_user} berhasil dibuat!")
                    except sqlite3.IntegrityError:
                        st.error("Username sudah terdaftar!")

# 📦 Modul Produk
def product_module():
    st.header("📦 Manajemen Produk")
    tab1, tab2, tab3 = st.tabs(["Daftar Produk", "Tambah Produk", "Stok Alert"])
    
    with tab1:
        conn = sqlite3.connect(BARANG_DB)
        df = pd.read_sql("SELECT * FROM products", conn)
        conn.close()
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "harga_modal": st.column_config.NumberColumn(format="Rp %d"),
                "harga_jual": st.column_config.NumberColumn(format="Rp %d")
            }
        )
    
    with tab2:
        with st.form("tambah_produk"):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Produk*")
                kategori = st.text_input("Kategori*")
                barcode = st.text_input("Barcode (Opsional)")
            with col2:
                modal = st.number_input("Harga Modal*", min_value=0)
                jual = st.number_input("Harga Jual*", min_value=0)
                stok = st.number_input("Stok Awal*", min_value=0)
            
            if st.form_submit_button("💾 Simpan Produk"):
                if not nama or not kategori:
                    st.warning("Nama dan kategori wajib diisi!")
                else:
                    try:
                        conn = sqlite3.connect(BARANG_DB)
                        c = conn.cursor()
                        c.execute("INSERT INTO products (nama, kategori, harga_modal, harga_jual, stok, barcode) VALUES (?, ?, ?, ?, ?, ?)",
                                 (nama, kategori, modal, jual, stok, barcode))
                        conn.commit()
                        conn.close()
                        st.success(f"Produk {nama} berhasil ditambahkan!")
                    except sqlite3.IntegrityError:
                        st.error("Barcode sudah terdaftar untuk produk lain!")
    
    with tab3:
        conn = sqlite3.connect(BARANG_DB)
        low_stock = pd.read_sql("SELECT nama, stok FROM products WHERE stok <= min_stok ORDER BY stok ASC", conn)
        conn.close()
        
        if not low_stock.empty:
            st.warning("🚨 Produk dengan Stok Menipis:")
            st.dataframe(low_stock, hide_index=True)
        else:
            st.success("✅ Semua stok produk aman")

# 🛒 Modul Transaksi
def transaction_module():
    st.header("🛒 Transaksi Penjualan")
    
    # Inisialisasi keranjang
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Pencarian Produk
        conn = sqlite3.connect(BARANG_DB)
        df_products = pd.read_sql("SELECT id, nama, harga_jual, stok FROM products WHERE stok > 0", conn)
        conn.close()
        
        selected_product = st.selectbox(
            "🔍 Cari Produk",
            df_products['nama'],
            index=None,
            placeholder="Pilih produk..."
        )
        
        if selected_product:
            product_data = df_products[df_products['nama'] == selected_product].iloc[0]
            
            col_qty, col_price = st.columns(2)
            with col_qty:
                qty = st.number_input(
                    "Jumlah",
                    min_value=1,
                    max_value=int(product_data['stok']),
                    value=1
                )
            with col_price:
                st.metric("Harga Satuan", f"Rp {product_data['harga_jual']:,.0f}")
            
            if st.button("➕ Tambah ke Keranjang", type="primary"):
                st.session_state.cart.append({
                    'id': product_data['id'],
                    'nama': product_data['nama'],
                    'harga': product_data['harga_jual'],
                    'qty': qty,
                    'subtotal': product_data['harga_jual'] * qty
                })
                st.success(f"{qty} {selected_product} ditambahkan ke keranjang!")
                st.rerun()
    
    with col2:
        # Ringkasan Pembayaran
        st.subheader("📝 Keranjang Belanja")
        
        if not st.session_state.cart:
            st.info("Keranjang kosong")
        else:
            total = sum(item['subtotal'] for item in st.session_state.cart)
            
            for i, item in enumerate(st.session_state.cart):
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.write(f"{item['nama']}")
                with cols[1]:
                    st.write(f"{item['qty']} x Rp {item['harga']:,.0f}")
                with cols[2]:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
            
            st.divider()
            
            # Pengaturan Diskon & Pajak
            with st.expander("⚙️ Pengaturan Pembayaran"):
                diskon = st.number_input("Diskon (%)", min_value=0, max_value=100, value=0)
                pajak = st.number_input("Pajak (%)", min_value=0, max_value=10, value=0)
            
            # Hitung Total
            total_diskon = total * diskon / 100
            total_pajak = (total - total_diskon) * pajak / 100
            grand_total = total - total_diskon + total_pajak
            
            st.metric("TOTAL PEMBAYARAN", f"Rp {grand_total:,.0f}", delta=f"Diskon: Rp {total_diskon:,.0f}")
            
            # Pembayaran
            pembayaran = st.number_input(
                "💵 Uang Diterima",
                min_value=0.0,
                value=float(grand_total),
                step=1000.0
            )
            
            if pembayaran < grand_total:
                st.error("Uang tidak cukup!")
            else:
                kembalian = pembayaran - grand_total
                st.metric("Kembalian", f"Rp {kembalian:,.0f}")
                
                if st.button("💳 Proses Pembayaran", type="primary"):
                    process_payment(
                        items=st.session_state.cart,
                        subtotal=total,
                        diskon=total_diskon,
                        pajak=total_pajak,
                        total=grand_total,
                        pembayaran=pembayaran,
                        kembalian=kembalian
                    )
                    st.session_state.cart = []
                    st.rerun()

def process_payment(items, subtotal, diskon, pajak, total, pembayaran, kembalian):
    """Simpan transaksi ke database"""
    try:
        conn = sqlite3.connect(TRANSAKSI_DB)
        c = conn.cursor()
        
        # Simpan transaksi
        c.execute("""
            INSERT INTO transactions 
            (waktu, items, subtotal, diskon, pajak, total, pembayaran, kembalian, user) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            json.dumps(items),
            subtotal,
            diskon,
            pajak,
            total,
            pembayaran,
            kembalian,
            st.session_state.user
        ))
        
        # Update stok produk
        for item in items:
            c.execute("""
                UPDATE products 
                SET stok = stok - ?, 
                    terjual = terjual + ? 
                WHERE id = ?
            """, (item['qty'], item['qty'], item['id']))
        
        conn.commit()
        conn.close()
        
        # Generate struk
        generate_receipt(items, subtotal, diskon, pajak, total, pembayaran, kembalian)
        st.success("✅ Transaksi berhasil diproses!")
        st.balloons()
        
    except Exception as e:
        st.error(f"Gagal memproses transaksi: {str(e)}")

def generate_receipt(items, subtotal, diskon, pajak, total, pembayaran, kembalian):
    """Generate struk transaksi"""
    receipt = [
        "TOKO WAWAN",
        "Jl. Contoh No. 123",
        "=" * 30,
        f"Kasir: {st.session_state.user}",
        f"Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "-" * 30
    ]
    
    for item in items:
        receipt.append(f"{item['nama'][:20]:<20} {item['qty']:>2}x {item['harga']:>7,.0f}")
        receipt.append(f"{' ':>20} Rp {item['subtotal']:>7,.0f}")
    
    receipt.extend([
        "-" * 30,
        f"Subtotal: Rp {subtotal:>7,.0f}",
        f"Diskon: Rp {diskon:>7,.0f}",
        f"Pajak: Rp {pajak:>7,.0f}",
        f"Total: Rp {total:>7,.0f}",
        f"Bayar: Rp {pembayaran:>7,.0f}",
        f"Kembali: Rp {kembalian:>7,.0f}",
        "=" * 30,
        "Terima kasih telah berbelanja!",
        "Barang yang sudah dibeli tidak dapat dikembalikan"
    ])
    
    # Tampilkan struk
    st.subheader("📃 Struk Transaksi")
    st.code("\n".join(receipt))
    
    # Download button
    st.download_button(
        label="⬇️ Download Struk",
        data="\n".join(receipt),
        file_name=f"struk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# 📊 Modul Laporan
def report_module():
    st.header("📊 Laporan Penjualan")
    
    # Filter tanggal
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Dari Tanggal", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("Sampai Tanggal", datetime.now())
    
    # Ambil data transaksi
    conn = sqlite3.connect(TRANSAKSI_DB)
    query = f"""
        SELECT * FROM transactions 
        WHERE date(waktu) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY waktu DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        st.warning("Tidak ada transaksi pada periode ini")
        return
    
    # Konversi items dari JSON ke dataframe
    df_items = pd.json_normalize(df['items'].apply(json.loads).explode('items')
    df_items = pd.json_normalize(df_items['items'])
    
    # Tampilkan ringkasan
    st.subheader("📈 Ringkasan")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi", len(df))
    col2.metric("Total Pendapatan", f"Rp {df['total'].sum():,.0f}")
    col3.metric("Rata-rata per Transaksi", f"Rp {df['total'].mean():,.0f}")
    
    # Grafik
    st.subheader("📊 Visualisasi Data")
    tab1, tab2 = st.tabs(["Trend Harian", "Produk Terlaris"])
    
    with tab1:
        df['tanggal'] = pd.to_datetime(df['waktu']).dt.date
        daily_sales = df.groupby('tanggal')['total'].sum().reset_index()
        
        fig = px.line(
            daily_sales, 
            x='tanggal', 
            y='total',
            title="Trend Penjualan Harian",
            labels={'tanggal': 'Tanggal', 'total': 'Total Penjualan'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        top_products = df_items.groupby('nama').agg({
            'qty': 'sum',
            'subtotal': 'sum'
        }).sort_values('qty', ascending=False).head(10)
        
        fig = px.bar(
            top_products,
            x='qty',
            y=top_products.index,
            orientation='h',
            title="10 Produk Terlaris",
            labels={'qty': 'Jumlah Terjual'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabel detail transaksi
    st.subheader("📋 Detail Transaksi")
    st.dataframe(df, hide_index=True, use_container_width=True)

# ==============================================
# 🚀 MAIN APP
# ==============================================
def main():
    init_db()
    auto_backup()
    
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login_module()
    else:
        st.sidebar.title(f"👋 Halo, {st.session_state.user}!")
        st.sidebar.write(f"Role: **{st.session_state.role.upper()}**")
        
        menu_options = {
            "📦 Produk": product_module,
            "🛒 Transaksi": transaction_module,
            "📊 Laporan": report_module
        }
        
        selected = st.sidebar.radio("Menu", list(menu_options.keys()))
        menu_options[selected]()
        
        if st.sidebar.button("🔒 Logout"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
