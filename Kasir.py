# Aplikasi Kasir Toko dengan Streamlit (Lengkap dengan Login Akun Tetap)

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(page_title="Kasir Toko", layout="wide")

# =============================
# KONSTANTA DAN FILE
# =============================
AKUN_FILE = "akun.json"

# =============================
# UTILS LOGIN AKUN
# =============================
def load_akun():
    if not os.path.exists(AKUN_FILE):
        with open(AKUN_FILE, "w") as f:
            json.dump([], f)
    with open(AKUN_FILE, "r") as f:
        return json.load(f)

def simpan_akun(data):
    with open(AKUN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def tampilkan_login():
    st.title("🔐 Login Aplikasi Kasir")
    tab1, tab2 = st.tabs(["Login", "Daftar Akun Baru"])

    with tab1:
        akun_data = load_akun()
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.radio("Role", ["admin", "kasir"], horizontal=True)
        if st.button("Masuk"):
            cocok = next((a for a in akun_data if a["username"] == username and a["password"] == password and a["role"] == role), None)
            if cocok:
                st.session_state.login = True
                st.session_state.user = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Username/password salah atau role tidak sesuai.")

    with tab2:
        st.subheader("📋 Buat Akun Baru")
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Role", ["admin", "kasir"], horizontal=True, key="daftar_role")
        if st.button("Daftar"):
            akun_data = load_akun()
            if any(u["username"] == new_user for u in akun_data):
                st.warning("Username sudah digunakan.")
            else:
                akun_data.append({"username": new_user, "password": new_pass, "role": new_role})
                simpan_akun(akun_data)
                st.success("Akun berhasil dibuat, silakan login.")

# =============================
# CEK LOGIN DAN INISIALISASI
# =============================
if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

# =============================
# SETUP SESSION
# =============================
if "barang" not in st.session_state:
    st.session_state.barang = []
if "transaksi" not in st.session_state:
    st.session_state.transaksi = []

st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("🔒 Logout"):
    st.session_state.clear()
    st.rerun()

# =============================
# TAB SETUP
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Input Barang", "🛒 Kasir", "🧾 Riwayat", "📈 Dashboard", "📤 Ekspor"
])

# =============================
# TAB 1: Input Barang
# =============================
with tab1:
    if st.session_state.role != "admin":
        st.warning("Hanya admin yang dapat menambahkan barang.")
    else:
        st.header("📦 Tambah Barang Baru")
        with st.form("form_barang"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            harga_modal = st.number_input("Harga Modal", min_value=0)
            harga_jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok", min_value=0, step=1)
            submit = st.form_submit_button("➕ Simpan Barang")

            if submit and nama and kategori:
                st.session_state.barang.append({
                    "nama": nama,
                    "kategori": kategori,
                    "harga_modal": harga_modal,
                    "harga_jual": harga_jual,
                    "stok": stok,
                    "terjual": 0
                })
                st.success(f"Barang '{nama}' berhasil ditambahkan!")

        if st.session_state.barang:
            df = pd.DataFrame(st.session_state.barang)
            st.dataframe(df)

# =============================
# TAB 2: Kasir
# =============================
with tab2:
    st.header("🛒 Transaksi Kasir")
    if not st.session_state.barang:
        st.warning("Belum ada barang di stok.")
    else:
        df_all = pd.DataFrame(st.session_state.barang)
        kategori_unik = df_all["kategori"].unique().tolist()

        col1, col2 = st.columns([2, 3])

        with col1:
            kategori_pilih = st.selectbox("Pilih Kategori:", ["Semua"] + kategori_unik)
            df_filter = df_all if kategori_pilih == "Semua" else df_all[df_all["kategori"] == kategori_pilih]
            st.dataframe(df_filter)

        with col2:
            barang_dipilih = st.multiselect("Pilih Barang:", df_all["nama"].tolist())
            if barang_dipilih:
                qty_dict, subtotal_dict, total = {}, {}, 0
                for nama in barang_dipilih:
                    barang = next(b for b in st.session_state.barang if b["nama"] == nama)
                    qty = st.number_input(f"Jumlah '{nama}'", min_value=1, step=1, key=f"qty_{nama}")
                    subtotal = qty * barang["harga_jual"]
                    qty_dict[nama] = qty
                    subtotal_dict[nama] = subtotal
                    total += subtotal

                st.write("### Ringkasan Belanja")
                for nama in barang_dipilih:
                    st.write(f"- {nama} x {qty_dict[nama]} = Rp {subtotal_dict[nama]:,}")
                st.write(f"### Total: Rp {total:,}")

                bayar = st.number_input("Bayar (Rp)", min_value=0, step=1000)
                if st.button("💵 Proses Pembayaran"):
                    if bayar < total:
                        st.error("Uang tidak cukup.")
                    else:
                        kembali = bayar - total
                        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        for nama in barang_dipilih:
                            barang = next(b for b in st.session_state.barang if b["nama"] == nama)
                            jumlah = qty_dict[nama]
                            if jumlah <= barang["stok"]:
                                barang["stok"] -= jumlah
                                barang["terjual"] += jumlah
                                st.session_state.transaksi.append({
                                    "waktu": waktu,
                                    "nama": nama,
                                    "kategori": barang["kategori"],
                                    "jumlah": jumlah,
                                    "total": subtotal_dict[nama],
                                    "keuntungan": (barang["harga_jual"] - barang["harga_modal"]) * jumlah
                                })

                        for nama in barang_dipilih:
                            st.session_state.pop(f"qty_{nama}", None)

                        st.success("Transaksi berhasil!")
                        st.code(f"""
Waktu: {waktu}
Total: Rp {total:,}
Bayar: Rp {bayar:,}
Kembali: Rp {kembali:,}
Barang:
""" + "\n".join([f"- {n} x {qty_dict[n]} = Rp {subtotal_dict[n]:,}" for n in barang_dipilih]))

# =============================
# TAB 3: Riwayat
# =============================
with tab3:
    st.header("🧾 Riwayat Transaksi")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df_trx = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df_trx)

# =============================
# TAB 4: Dashboard
# =============================
with tab4:
    st.header("📈 Dashboard Penjualan")
    if not st.session_state.transaksi:
        st.info("Belum ada data transaksi.")
    else:
        df_trx = pd.DataFrame(st.session_state.transaksi)
        tab_a, tab_b = st.tabs(["📊 Grafik", "📋 Tabel"])

        with tab_a:
            fig1 = px.bar(df_trx.groupby("nama")["jumlah"].sum().reset_index(), x="nama", y="jumlah", title="Penjualan per Barang")
            fig2 = px.pie(df_trx, names="nama", values="keuntungan", title="Kontribusi Keuntungan per Barang")
            fig3 = px.bar(df_trx.groupby("kategori")["keuntungan"].sum().reset_index(), x="kategori", y="keuntungan", title="Keuntungan per Kategori")
            fig4 = px.bar(df_trx.groupby("kategori")["jumlah"].sum().reset_index(), x="kategori", y="jumlah", title="Penjualan per Kategori")
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.plotly_chart(fig3, use_container_width=True)
            st.plotly_chart(fig4, use_container_width=True)

        with tab_b:
            st.subheader("📋 Ringkasan Keuntungan")
            st.write("Total Keuntungan: Rp", df_trx["keuntungan"].sum())
            keuntungan_per_barang = df_trx.groupby("nama")["keuntungan"].sum().reset_index()
            keuntungan_per_kategori = df_trx.groupby("kategori")["keuntungan"].sum().reset_index()
            st.write("Keuntungan per Barang")
            st.dataframe(keuntungan_per_barang)
            st.write("Keuntungan per Kategori")
            st.dataframe(keuntungan_per_kategori)

# =============================
# TAB 5: Ekspor
# =============================
with tab5:
    st.header("📤 Ekspor Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.barang:
            df_barang = pd.DataFrame(st.session_state.barang)
            st.download_button("⬇️ Unduh Data Barang", df_barang.to_csv(index=False), file_name="barang.csv")
    with col2:
        if st.session_state.transaksi:
            df_transaksi = pd.DataFrame(st.session_state.transaksi)
            st.download_button("⬇️ Unduh Riwayat Transaksi", df_transaksi.to_csv(index=False), file_name="transaksi.csv")
