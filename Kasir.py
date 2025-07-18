# aplikasi_kasir.py
import streamlit as st
import pandas as pd
import json
import os
import shutil
from datetime import datetime
import plotly.express as px
import io

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"

def backup_file(file):
    """Backup file corrupt ke *_backup_TIMESTAMP.json"""
    if os.path.exists(file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file}_backup_{timestamp}"
        shutil.copy(file, backup_name)
        notify_warn(f"⚠️ File {file} corrupt! Dibackup ke {backup_name}")

def load_data(file, default=[]):
    """Load JSON, reset ke default jika kosong/corrupt"""
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False)
        return default
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        backup_file(file)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False)
        return default

def simpan_data(file, data):
    """Simpan data ke JSON"""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def notify_info(msg): st.info(msg.encode("utf-8").decode("utf-8"))
def notify_success(msg): st.success(msg.encode("utf-8").decode("utf-8"))
def notify_warn(msg): st.warning(msg.encode("utf-8").decode("utf-8"))
def notify_error(msg): st.error(msg.encode("utf-8").decode("utf-8"))

def load_akun(): return load_data(AKUN_FILE)
def simpan_akun(data): simpan_data(AKUN_FILE, data)

def tampilkan_login():
    st.title("🔒 Login Kasir")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Buat Akun Baru"])

    with tab1:
        data = load_akun()
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["admin", "kasir"], horizontal=True)
        if st.button("Masuk"):
            cocok = next((a for a in data if a["username"] == username and a["password"] == password and a["role"] == role), None)
            if cocok:
                st.session_state.login = True
                st.session_state.user = username
                st.session_state.role = role
                st.rerun()
            else:
                notify_error("Login gagal. Periksa username/password/role.")

    with tab2:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Pilih Role", ["admin", "kasir"], horizontal=True, key="daftar")
        if st.button("Daftar"):
            data = load_akun()
            if any(u["username"] == new_user for u in data):
                notify_warn("Username sudah ada.")
            else:
                data.append({"username": new_user, "password": new_pass, "role": new_role})
                simpan_akun(data)
                notify_success("Akun berhasil dibuat!")

if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

# Load data
st.session_state.barang = load_data(BARANG_FILE)
st.session_state.transaksi = load_data(TRANSAKSI_FILE)

st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("🔓 Logout"):
    st.session_state.clear()
    st.rerun()

menu = ["📦 Input Barang", "🛒 Kasir", "📋 Stok", "🧾 Riwayat", "📊 Dashboard", "📤 Ekspor"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(menu)

# 📦 Input Barang
with tab1:
    st.header("📦 Input Barang")
    if st.session_state.role != "admin":
        notify_warn("Hanya admin yang bisa menambahkan barang.")
    else:
        with st.form("form_barang"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            modal = st.number_input("Harga Modal", min_value=0)
            jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok Awal", min_value=0, step=1)
            simpan = st.form_submit_button("💾 Simpan Barang")
            if simpan and nama and kategori:
                st.session_state.barang.append({
                    "nama": nama,
                    "kategori": kategori,
                    "harga_modal": modal,
                    "harga_jual": jual,
                    "stok": stok,
                    "terjual": 0
                })
                simpan_data(BARANG_FILE, st.session_state.barang)
                notify_success(f"Barang '{nama}' disimpan.")

        if st.session_state.barang:
            st.dataframe(pd.DataFrame(st.session_state.barang))

# 🛒 Transaksi Kasir
with tab2:
    st.header("🛒 Transaksi Kasir")

    if not st.session_state.barang:
        notify_warn("Belum ada barang di stok.")
    else:
        df_barang = pd.DataFrame(st.session_state.barang)

        if "keranjang" not in st.session_state:
            st.session_state.keranjang = []

        cari_barang = st.text_input("🔍 Cari Barang")
        df_filtered = df_barang[df_barang["nama"].str.contains(cari_barang, case=False)] if cari_barang else df_barang

        if not df_filtered.empty:
            barang_pilih = st.selectbox("Pilih Barang", df_filtered["nama"])
            barang_data = df_filtered[df_filtered["nama"] == barang_pilih].iloc[0]
            jumlah_beli = st.number_input(f"Jumlah '{barang_pilih}'", min_value=1, max_value=int(barang_data["stok"]), step=1)

            if st.button("🛒 Tambah ke Keranjang"):
                st.session_state.keranjang.append({
                    "nama": barang_pilih,
                    "kategori": barang_data["kategori"],
                    "jumlah": jumlah_beli,
                    "harga_satuan": barang_data["harga_jual"],
                    "subtotal": jumlah_beli * barang_data["harga_jual"]
                })
                notify_success(f"{jumlah_beli} {barang_pilih} ditambahkan ke keranjang.")

        if st.session_state.keranjang:
            st.subheader("📝 Keranjang Belanja")
            for i, item in enumerate(st.session_state.keranjang):
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 2, 2, 1])
                col1.markdown(f"**{item['nama']}**")
                col2.markdown(f"Kategori: {item['kategori']}")
                col3.markdown(f"Jumlah: {item['jumlah']}")
                col4.markdown(f"Harga: Rp {item['harga_satuan']:,}")
                col5.markdown(f"Subtotal: Rp {item['subtotal']:,}")
                if col6.button("❌", key=f"hapus_cart_{i}"):
                    st.session_state.keranjang.pop(i)
                    st.rerun()

            total_bayar = sum(item["subtotal"] for item in st.session_state.keranjang)
            st.markdown(f"## 💵 Total Bayar: Rp {total_bayar:,}")

            uang_bayar = st.number_input("💵 Uang Diterima", min_value=0, step=1000)

            if st.button("✅ Proses Transaksi"):
                if uang_bayar < total_bayar:
                    notify_error("Uang tidak cukup.")
                else:
                    kembalian = uang_bayar - total_bayar
                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    for item in st.session_state.keranjang:
                        for b in st.session_state.barang:
                            if b["nama"] == item["nama"]:
                                b["stok"] -= item["jumlah"]
                                b["terjual"] += item["jumlah"]
                                keuntungan = (b["harga_jual"] - b["harga_modal"]) * item["jumlah"]
                                st.session_state.transaksi.append({
                                    "waktu": waktu,
                                    "nama": b["nama"],
                                    "kategori": b["kategori"],
                                    "jumlah": item["jumlah"],
                                    "total": item["subtotal"],
                                    "keuntungan": keuntungan,
                                    "user": st.session_state.user
                                })

                    simpan_data(BARANG_FILE, st.session_state.barang)
                    simpan_data(TRANSAKSI_FILE, st.session_state.transaksi)

                    struk = io.StringIO()
                    struk.write("TOKO WAWAN\nJl. Contoh No. 1, Telp. 0812-XXXX-XXXX\n")
                    struk.write("="*32 + "\n")
                    struk.write(f"Waktu : {waktu}\n")
                    struk.write("-"*32 + "\n")
                    for item in st.session_state.keranjang:
                        struk.write(f"{item['nama']} x{item['jumlah']} @{item['harga_satuan']:,}\n")
                        struk.write(f"       Rp {item['subtotal']:,}\n")
                    struk.write("-"*32 + "\n")
                    struk.write(f"Subtotal : Rp {total_bayar:,}\n")
                    struk.write(f"Bayar    : Rp {uang_bayar:,}\n")
                    struk.write(f"Kembalian: Rp {kembalian:,}\n")
                    struk.write("="*32 + "\nTerima kasih atas kunjungan Anda\n")

                    notify_success("✅ Transaksi berhasil.")
                    st.text(struk.getvalue())
                    st.download_button("🖨️ Download Struk", data=struk.getvalue(), file_name="struk_toko_wawan.txt")
                    st.session_state.keranjang.clear()
# 🧾 Riwayat Transaksi
with tab4:
    st.header("🧾 Riwayat Transaksi")
    df_transaksi = pd.DataFrame(st.session_state.transaksi)
    if df_transaksi.empty:
        notify_info("Belum ada transaksi.")
    else:
        df_transaksi["waktu"] = pd.to_datetime(df_transaksi["waktu"])
        tanggal_mulai = st.date_input("Dari Tanggal", df_transaksi["waktu"].min().date())
        tanggal_akhir = st.date_input("Sampai Tanggal", df_transaksi["waktu"].max().date())
        mask = (df_transaksi["waktu"].dt.date >= tanggal_mulai) & (df_transaksi["waktu"].dt.date <= tanggal_akhir)
        df_filtered = df_transaksi[mask]

        if st.session_state.role == "kasir":
            df_filtered = df_filtered[df_filtered["user"] == st.session_state.user]

        st.dataframe(df_filtered)

        # Ringkasan Total
        total_transaksi = df_filtered["total"].sum()
        total_keuntungan = df_filtered["keuntungan"].sum()
        notify_success(f"✅ Total Transaksi: Rp {total_transaksi:,} | Keuntungan: Rp {total_keuntungan:,}")

# 📊 Dashboard
with tab5:
    st.header("📊 Dashboard")
    df_dashboard = pd.DataFrame(st.session_state.transaksi)
    if df_dashboard.empty:
        notify_info("Belum ada transaksi.")
    else:
        tab_chart, tab_table = st.tabs(["📈 Grafik", "📋 Tabel"])
        with tab_chart:
            fig1 = px.bar(
                df_dashboard.groupby("nama")["jumlah"].sum().reset_index(),
                x="nama", y="jumlah", title="📊 Penjualan per Barang"
            )
            fig2 = px.pie(
                df_dashboard, names="nama", values="keuntungan",
                title="📊 Kontribusi Keuntungan per Barang"
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
        with tab_table:
            df_summary = df_dashboard.groupby("nama")[["jumlah", "keuntungan"]].sum().reset_index()
            st.dataframe(df_summary)

# 📤 Ekspor Data
with tab6:
    st.header("📤 Ekspor Data")
    col_barang, col_transaksi = st.columns(2)

    with col_barang:
        if st.session_state.barang:
            df_barang = pd.DataFrame(st.session_state.barang)
            csv_barang = df_barang.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Unduh Data Barang",
                data=csv_barang,
                file_name="data_barang.csv",
                mime="text/csv"
            )
    with col_transaksi:
        if st.session_state.transaksi:
            df_transaksi_all = pd.DataFrame(st.session_state.transaksi)
            csv_transaksi = df_transaksi_all.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Unduh Data Transaksi",
                data=csv_transaksi,
                file_name="data_transaksi.csv",
                mime="text/csv"
            )
