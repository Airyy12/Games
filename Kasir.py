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
import plotly.express as px
import base64

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

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

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
                    "role": "admin",
                    "nama_lengkap": "",
                    "no_telepon": "",
                    "foto_profil": None
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
                st.session_state.login = {
                    "username": username,
                    "role": a["role"]
                }
                st.success("Login berhasil!")
                st.rerun()
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
        jumlah_hapus = st.number_input("Jumlah yang Dihapus", min_value=1, max_value=barang[index]['stok'], step=1)
        keterangan = st.text_input("Alasan Penghapusan")
        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.code(tanggal, language="text")
        if st.button("Hapus Barang"):
            barang_dihapus = load_data(BARANG_HAPUS_FILE)
            data_dihapus = barang[index].copy()
            data_dihapus.update({
                "jumlah_dihapus": jumlah_hapus,
                "keterangan": keterangan,
                "tanggal_dihapus": tanggal,
                "dihapus_oleh": st.session_state.login["username"]
            })

            if jumlah_hapus == barang[index]["stok"]:
                barang.pop(index)
            else:
                barang[index]["stok"] -= jumlah_hapus

            barang_dihapus.append(data_dihapus)
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

    qty = st.number_input(f"Jumlah ({b_dipilih['stok']} tersedia)", 1, b_dipilih['stok'])

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    if st.button("➕ Tambah ke Keranjang"):
        existing = next((item for item in st.session_state.keranjang
                         if item['nama'] == b_dipilih['nama'] and item['kategori'] == b_dipilih['kategori']), None)
        if existing:
            existing['qty'] += qty
            existing['subtotal'] = existing['qty'] * existing['harga']
        else:
            st.session_state.keranjang.append({
                "nama": b_dipilih['nama'],
                "kategori": b_dipilih['kategori'],
                "qty": qty,
                "harga": b_dipilih['harga'],
                "harga_modal": b_dipilih.get("harga_modal", 0),
                "subtotal": b_dipilih['harga'] * qty
            })

    if st.session_state.get("keranjang"):
        st.write("### 🧺 Keranjang Belanja")
        total = 0
        for idx, item in enumerate(st.session_state.keranjang):
            with st.container():
                st.markdown("---")
                cols = st.columns([3, 2, 2, 2, 2, 1])
                cols[0].markdown(f"**{item['nama']}**\nKategori: {item['kategori']}")
                cols[1].markdown(f"Qty: **{item['qty']}**")
                cols[2].markdown(f"Harga: **Rp {item['harga']:,.0f}**")
                cols[3].markdown(f"Subtotal: **Rp {item['subtotal']:,.0f}**")
                hapus_qty = cols[4].number_input("Jumlah Hapus", min_value=1, max_value=item['qty'], value=1, key=f"hapus_qty_{idx}")
                if cols[5].button("❌", key=f"hapus_btn_{idx}"):
                    if hapus_qty >= item['qty']:
                        st.session_state.keranjang.pop(idx)
                    else:
                        item['qty'] -= hapus_qty
                        item['subtotal'] = item['qty'] * item['harga']
                    st.experimental_rerun()
            total += item['subtotal']

        st.markdown("---")
        st.markdown(f"### 💰 Total: Rp {total:,.0f}")

        metode = st.radio("Pilih Metode Pembayaran", ["Cash", "QRIS/Transfer"])

        uang_dibayar = 0
        kembalian = 0
        if metode == "Cash":
            uang_dibayar = st.number_input("💵 Uang Diterima", min_value=0)
            if uang_dibayar >= total:
                kembalian = uang_dibayar - total
                st.success(f"Kembalian: Rp {kembalian:,.0f}")
            else:
                st.warning("Uang diterima kurang dari total belanja.")

        if metode == "QRIS/Transfer" or uang_dibayar >= total:
            if st.button("💾 Simpan Transaksi"):
                # Update stok
                for item in st.session_state.keranjang:
                    for b in barang:
                        if b["nama"] == item["nama"] and b["kategori"] == item["kategori"]:
                            b["stok"] -= item["qty"]

                # Simpan transaksi
                transaksi_baru = {
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "kasir": st.session_state.login["username"],
                    "items": st.session_state.keranjang.copy(),
                    "total": total,
                    "bayar": uang_dibayar if metode == "Cash" else total,
                    "kembalian": kembalian,
                    "metode": metode
                }
                transaksi.append(transaksi_baru)
                save_data(BARANG_FILE, barang)
                save_data(TRANSAKSI_FILE, transaksi)

                st.success("Transaksi berhasil disimpan ✅")

                # Tampilkan struk
                st.markdown("---")
                st.subheader("🧾 Struk Transaksi")
                st.write(f"**Waktu**: {transaksi_baru['waktu']}")
                st.write(f"**Kasir**: {transaksi_baru['kasir']}")
                st.write(f"**Metode**: {transaksi_baru['metode']}")
                for item in transaksi_baru['items']:
                    st.write(f"- {item['nama']} ({item['qty']}x): Rp {item['subtotal']:,.0f}")
                st.write(f"**Total**: Rp {transaksi_baru['total']:,.0f}")
                st.write(f"**Dibayar**: Rp {transaksi_baru['bayar']:,.0f}")
                st.write(f"**Kembalian**: Rp {transaksi_baru['kembalian']:,.0f}")

                # Reset keranjang
                st.session_state.keranjang = []

def halaman_riwayat():
    st.subheader("📜 Riwayat Transaksi")
    transaksi = load_data(TRANSAKSI_FILE)

    if not transaksi:
        st.info("Belum ada transaksi.")
    else:
        # Format kolom 'items'
        for t in transaksi:
            t["items"] = ", ".join(f"{item['nama']}({item['qty']}x)" for item in t["items"])

        df = pd.DataFrame(transaksi)
        df["waktu"] = pd.to_datetime(df["waktu"])

        # Filter tanggal transaksi
        st.markdown("### 🔎 Filter Transaksi")
        tanggal_mulai = st.date_input("📅 Tanggal Mulai", df["waktu"].min().date(), key="transaksi_mulai")
        tanggal_akhir = st.date_input("📅 Tanggal Akhir", df["waktu"].max().date(), key="transaksi_akhir")
        mask = (df["waktu"].dt.date >= tanggal_mulai) & (df["waktu"].dt.date <= tanggal_akhir)
        df_filtered = df[mask]

        st.dataframe(df_filtered)

    st.subheader("🗑️ Riwayat Penghapusan Barang")
    hapus = load_data(BARANG_HAPUS_FILE)
    if not hapus:
        st.info("Belum ada riwayat penghapusan.")
    else:
        df_hapus = pd.DataFrame(hapus)
        df_hapus["tanggal_dihapus"] = pd.to_datetime(df_hapus["tanggal_dihapus"])

        # Filter tanggal penghapusan
        st.markdown("### 🔎 Filter Penghapusan Barang")
        hapus_mulai = st.date_input("📅 Tanggal Mulai", df_hapus["tanggal_dihapus"].min().date(), key="hapus_mulai")
        hapus_akhir = st.date_input("📅 Tanggal Akhir", df_hapus["tanggal_dihapus"].max().date(), key="hapus_akhir")
        hapus_mask = (df_hapus["tanggal_dihapus"].dt.date >= hapus_mulai) & (df_hapus["tanggal_dihapus"].dt.date <= hapus_akhir)
        df_hapus_filtered = df_hapus[hapus_mask]

        st.dataframe(df_hapus_filtered)

def halaman_laporan():
    st.subheader("📈 Laporan Keuangan")
    data = load_data(TRANSAKSI_FILE)
    
    if not data:
        st.info("Belum ada data transaksi.")
        return

    df = pd.DataFrame(data)
    df['waktu'] = pd.to_datetime(df['waktu'])
    df['tanggal'] = df['waktu'].dt.date
    df['bulan'] = df['waktu'].dt.strftime('%Y-%m')

    # Filter Tanggal
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", df['tanggal'].min())
    with col2:
        end_date = st.date_input("Tanggal Akhir", df['tanggal'].max())

    df_filtered = df[(df['tanggal'] >= start_date) & (df['tanggal'] <= end_date)]

    # Ringkasan Pendapatan
    st.write("### 📊 Ringkasan Pendapatan")
    total_pendapatan = df_filtered['total'].sum()
    rata_perhari = df_filtered.groupby('tanggal')['total'].sum().mean() if not df_filtered.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col2.metric("Rata-rata per Hari", f"Rp {rata_perhari:,.0f}")
    col3.metric("Jumlah Transaksi", len(df_filtered))

    # Pendapatan per Kasir
    st.write("### 🧑‍💼 Pendapatan per Kasir")
    kasir_df = df_filtered.groupby('kasir')['total'].agg(['sum', 'count']).reset_index()
    kasir_df.columns = ['Kasir', 'Total Pendapatan', 'Jumlah Transaksi']
    st.dataframe(kasir_df, hide_index=True)

    # Export Laporan
    if st.button("💾 Ekspor ke Excel"):
        with pd.ExcelWriter("laporan_penjualan.xlsx") as writer:
            df_filtered.to_excel(writer, sheet_name="Transaksi", index=False)
            kasir_df.to_excel(writer, sheet_name="Kasir", index=False)
        st.success("Laporan berhasil di-generate!")

def halaman_statistik():
    st.subheader("📊 Statistik Penjualan")
    data = load_data(TRANSAKSI_FILE)
    
    if not data:
        st.info("Belum ada data transaksi.")
        return

    df = pd.DataFrame(data)
    df['waktu'] = pd.to_datetime(df['waktu'])
    df['tanggal'] = df['waktu'].dt.date
    df['bulan'] = df['waktu'].dt.strftime('%Y-%m')

    # Filter Tanggal
    min_date = df['tanggal'].min() if not df.empty else datetime.now().date()
    max_date = df['tanggal'].max() if not df.empty else datetime.now().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", min_date, key="stat_start")
    with col2:
        end_date = st.date_input("Tanggal Akhir", max_date, key="stat_end")

    df_filtered = df[(df['tanggal'] >= start_date) & (df['tanggal'] <= end_date)]

    # Grafik Pendapatan Harian
    st.write("### 📈 Pendapatan Harian")
    daily_income = df_filtered.groupby('tanggal')['total'].sum().reset_index()
    if not daily_income.empty:
        fig = px.line(
            daily_income,
            x='tanggal',
            y='total',
            title="Pendapatan Harian",
            labels={'tanggal': 'Tanggal', 'total': 'Pendapatan (Rp)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Tidak ada data pendapatan di rentang tanggal ini.")

    # Grafik Barang Terlaris
    st.write("### 🏆 Barang Terlaris")
    all_items = []
    for t in data:
        for item in t['items']:
            all_items.append(item['nama'])
    
    if all_items:
        item_counts = pd.Series(all_items).value_counts().reset_index()
        item_counts.columns = ['Barang', 'Jumlah Terjual']
        fig = px.bar(
            item_counts.head(10),
            x='Barang',
            y='Jumlah Terjual',
            title="10 Barang Terlaris"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Belum ada barang yang terjual.")

def halaman_profil(username=None):
    # Default ke user yang login jika tidak ada parameter
    target_user = username if username else st.session_state.login["username"]
    is_admin = st.session_state.login["role"] == "admin"
    is_own_profile = target_user == st.session_state.login["username"]
    
    st.subheader(f"👤 Profil {target_user}")
    akun = load_data(AKUN_FILE)
    user_data = next((a for a in akun if a["username"] == target_user), None)

    if not user_data:
        st.error("Data pengguna tidak ditemukan")
        return

    # Inisialisasi data jika kosong
    user_data.setdefault("nama_lengkap", "")
    user_data.setdefault("no_telepon", "")
    user_data.setdefault("foto_profil", None)

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### Foto Profil")
        if user_data["foto_profil"]:
            try:
                # Decode base64 image
                image_data = base64.b64decode(user_data["foto_profil"])
                image = Image.open(io.BytesIO(image_data))
                st.image(image, width=150)
            except:
                st.warning("Gagal memuat foto profil")
        
        if is_own_profile:
            uploaded_file = st.file_uploader("Ubah foto profil", type=["jpg", "png", "jpeg"], key=f"upload_{target_user}")
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    # Resize image to max 300px width
                    width, height = image.size
                    if width > 300:
                        ratio = 300 / width
                        image = image.resize((300, int(height * ratio)))
                    
                    # Convert to base64
                    user_data["foto_profil"] = image_to_base64(image)
                    save_data(AKUN_FILE, akun)
                    st.success("Foto profil berhasil diperbarui!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memproses gambar: {str(e)}")
            
            if user_data["foto_profil"] and st.button("Hapus Foto Profil", key=f"delete_{target_user}"):
                user_data["foto_profil"] = None
                save_data(AKUN_FILE, akun)
                st.success("Foto profil dihapus!")
                st.rerun()
    
    with col2:
        st.write("### Informasi Pengguna")
        st.text_input("Username", value=user_data["username"], disabled=True)
        
        # Hanya admin atau pemilik profil yang bisa edit
        if is_admin or is_own_profile:
            nama_lengkap = st.text_input("Nama Lengkap", value=user_data["nama_lengkap"], 
                                       disabled=not (is_admin or is_own_profile))
            no_telepon = st.text_input("Nomor Telepon", value=user_data["no_telepon"], 
                                     disabled=not is_admin)  # Hanya admin yang bisa edit no telepon
            
            if st.button("Simpan Perubahan", key=f"save_{target_user}"):
                user_data["nama_lengkap"] = nama_lengkap
                user_data["no_telepon"] = no_telepon
                save_data(AKUN_FILE, akun)
                st.success("Profil berhasil diperbarui!")
        else:
            st.text_input("Nama Lengkap", value=user_data["nama_lengkap"], disabled=True)
            st.text_input("Nomor Telepon", value=user_data["no_telepon"], disabled=True)
        
        st.text_input("Role", value=user_data["role"], disabled=True)
    
    st.markdown("---")
    st.write("### 📊 Statistik Performa")
    
    # Load transaction data
    try:
        transaksi = load_data(TRANSAKSI_FILE)
        if not transaksi:
            st.info("Belum ada data transaksi.")
            return
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return

    # Konversi ke DataFrame
    try:
        df = pd.DataFrame(transaksi)
        df['waktu'] = pd.to_datetime(df['waktu'])
        df['tanggal'] = df['waktu'].dt.date
        df['bulan'] = df['waktu'].dt.strftime('%Y-%m')
    except Exception as e:
        st.error(f"Error memproses data: {str(e)}")
        return

    # Filter hanya transaksi pengguna saat ini
    transaksi_saya = df[df['kasir'] == target_user]
    
    if transaksi_saya.empty:
        st.info("Pengguna ini belum melakukan transaksi.")
        return
    
    # 1. Statistik Dasar
    st.write("#### 📌 Ringkasan")
    total_transaksi = len(transaksi_saya)
    total_pendapatan = transaksi_saya['total'].sum()
    rata_transaksi = transaksi_saya['total'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi", total_transaksi)
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col3.metric("Rata-rata/Transaksi", f"Rp {rata_transaksi:,.0f}")

    # 2. Grafik Performa Bulanan
    st.write("### 📈 Grafik Performa")
    try:
        bulanan = transaksi_saya.groupby('bulan').agg({
            'total': 'sum',
            'waktu': 'count'
        }).rename(columns={'total': 'Pendapatan', 'waktu': 'Jumlah Transaksi'})
        
        fig = px.bar(
            bulanan,
            x=bulanan.index,
            y='Pendapatan',
            title='Pendapatan Bulanan',
            labels={'bulan': 'Bulan', 'Pendapatan': 'Total Pendapatan (Rp)'},
            text_auto='.2s',
            color='Jumlah Transaksi',
            color_continuous_scale='blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal membuat grafik: {str(e)}")

def halaman_akun():
    st.subheader("👥 Manajemen Pengguna")
    
    akun = load_data(AKUN_FILE)
    current_user = st.session_state.login["username"]
    
    # Hanya admin yang bisa menambah akun baru
    if st.session_state.login["role"] == "admin":
        with st.expander("➕ Tambah Akun Baru", expanded=False):
            with st.form("form_akun_baru"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["admin", "kasir"])
                
                if st.form_submit_button("Buat Akun"):
                    if any(a["username"] == username for a in akun):
                        st.error("Username sudah digunakan!")
                    else:
                        akun.append({
                            "username": username,
                            "password": hash_password(password),
                            "role": role,
                            "nama_lengkap": "",
                            "no_telepon": "",
                            "foto_profil": None
                        })
                        save_data(AKUN_FILE, akun)
                        st.success("Akun berhasil dibuat!")
                        st.rerun()
    
    st.write("### Daftar Pengguna")
    if not akun:
        st.info("Belum ada akun terdaftar")
        return
    
    # Tampilkan daftar pengguna tanpa password
    df = pd.DataFrame(akun).drop(columns=["password"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Pilih pengguna untuk dilihat/diedit
    st.write("### Edit Profil Pengguna")
    user_list = [a["username"] for a in akun]
    selected_user = st.selectbox("Pilih Pengguna", user_list)
    
    if selected_user:
        halaman_profil(username=selected_user)

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
    "Statistik": halaman_statistik,
    "Profil Saya": halaman_profil
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

    st.markdown('<div class="sidebar-title">\U0001F4CB <span>Kasir App</span></div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="margin-bottom: 12px;">
            \U0001F464 Login sebagai: <span class="user-badge">{st.session_state.login['username']}</span><br>
            ({st.session_state.login['role']})
        </div>
    """, unsafe_allow_html=True)

    menu_icon = {
        "Dashboard": "📊",
        "Barang": "📦",
        "Transaksi": "🛒",
        "Riwayat": "📜",
        "Laporan": "📈",
        "Statistik": "📊",
        "Profil Saya": "👤",
        "Manajemen Akun": "👥"
    }
    
    # Hanya tampilkan menu yang sesuai dengan role
    available_menus = list(menu.keys())
    if st.session_state["login"]["role"] != "admin":
        available_menus.remove("Manajemen Akun")
    
    pilihan = st.radio("\U0001F4CC Menu", [f"{menu_icon[m]} {m}" for m in available_menus])

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("\U0001F513 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logout berhasil.")
        st.rerun()

menu_label = pilihan.split(" ", 1)[1]
st.title("Aplikasi Kasir")
menu[menu_label]()
