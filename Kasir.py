# aplikasi_kasir.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import io

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"

def load_data(file, default=[]):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def simpan_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def load_akun():
    return load_data(AKUN_FILE)

def simpan_akun(data):
    simpan_data(AKUN_FILE, data)

def tampilkan_login():
    st.title("\U0001F510 Login Kasir")
    tab1, tab2 = st.tabs(["Login", "Buat Akun Baru"])

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
                st.error("Login gagal. Periksa username/password/role.")

    with tab2:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.radio("Pilih Role", ["admin", "kasir"], horizontal=True, key="daftar")
        if st.button("Daftar"):
            data = load_akun()
            if any(u["username"] == new_user for u in data):
                st.warning("Username sudah ada.")
            else:
                data.append({"username": new_user, "password": new_pass, "role": new_role})
                simpan_akun(data)
                st.success("Akun berhasil dibuat!")

if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

if "barang" not in st.session_state:
    st.session_state.barang = load_data(BARANG_FILE)
if "transaksi" not in st.session_state:
    st.session_state.transaksi = load_data(TRANSAKSI_FILE)

st.sidebar.title("\U0001F464 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("\U0001F512 Logout"):
    st.session_state.clear()
    st.rerun()

menu = ["\U0001F4E6 Input Barang", "\U0001F6D2 Kasir", "\U0001F4CB Stok", "\U0001F9FE Riwayat", "\U0001F4C8 Dashboard", "\U0001F4E4 Ekspor"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(menu)

# ======================
# 📦 INPUT BARANG
# ======================
with tab1:
    st.header("\U0001F4E6 Input Barang")
    if st.session_state.role != "admin":
        st.warning("Hanya admin yang bisa menambahkan barang.")
    else:
        with st.form("form_barang"):
            nama = st.text_input("Nama Barang")
            kategori = st.text_input("Kategori")
            modal = st.number_input("Harga Modal", min_value=0)
            jual = st.number_input("Harga Jual", min_value=0)
            stok = st.number_input("Stok Awal", min_value=0, step=1)
            simpan = st.form_submit_button("Simpan Barang")
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
                st.success(f"Barang '{nama}' disimpan.")

        if st.session_state.barang:
            st.dataframe(pd.DataFrame(st.session_state.barang))

# ======================
# 🛒 KASIR
# ======================
with tab2:
    st.header("\U0001F6D2 Transaksi Kasir")

    if not st.session_state.barang:
        st.warning("Belum ada barang di stok.")
    else:
        df_barang = pd.DataFrame(st.session_state.barang)

        if "keranjang" not in st.session_state:
            st.session_state.keranjang = []

        cari_barang = st.text_input("\U0001F50D Cari Barang")
        df_filtered = df_barang[df_barang["nama"].str.contains(cari_barang, case=False)] if cari_barang else df_barang

        if not df_filtered.empty:
            barang_pilih = st.selectbox("Pilih Barang", df_filtered["nama"])
            barang_data = df_filtered[df_filtered["nama"] == barang_pilih].iloc[0]
            jumlah_beli = st.number_input(f"Jumlah '{barang_pilih}'", min_value=1, max_value=int(barang_data["stok"]), step=1)

            if st.button("\U0001F6D2 Tambah ke Keranjang"):
                st.session_state.keranjang.append({
                    "nama": barang_pilih,
                    "kategori": barang_data["kategori"],
                    "jumlah": jumlah_beli,
                    "harga_satuan": barang_data["harga_jual"],
                    "subtotal": jumlah_beli * barang_data["harga_jual"]
                })
                st.success(f"{jumlah_beli} {barang_pilih} ditambahkan ke keranjang.")

        if st.session_state.keranjang:
            st.subheader("\U0001F4DD Keranjang Belanja")

            for i, item in enumerate(st.session_state.keranjang):
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 2, 2, 1])
                col1.markdown(f"**{item['nama']}**")
                col2.markdown(f"Kategori: {item['kategori']}")
                col3.markdown(f"Jumlah: {item['jumlah']}")
                col4.markdown(f"Harga: Rp {item['harga_satuan']:,}")
                col5.markdown(f"Subtotal: Rp {item['subtotal']:,}")
                if col6.button("\u274C", key=f"hapus_{i}"):
                    st.session_state.keranjang.pop(i)
                    st.rerun()

            total_bayar = sum(item["subtotal"] for item in st.session_state.keranjang)
            st.markdown(f"## \U0001F4B0 Total Bayar: Rp {total_bayar:,}")

            uang_bayar = st.number_input("\U0001F4B5 Uang Diterima", min_value=0, step=1000)

            if st.button("\u2705 Proses Transaksi"):
                if uang_bayar < total_bayar:
                    st.error("Uang tidak cukup.")
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
                    struk.write("TOKO WAWAN\n")
                    struk.write("Jl. Contoh No. 1, Telp. 0812-XXXX-XXXX\n")
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
                    struk.write("="*32 + "\n")
                    struk.write("Terima kasih atas kunjungan Anda\n")

                    st.success("\u2705 Transaksi berhasil.")
                    st.text(struk.getvalue())
                    st.download_button("\U0001F5A8️ Download Struk", data=struk.getvalue(), file_name="struk_toko_wawan.txt")
                    st.session_state.keranjang.clear()

# ======================
# 📋 STATUS STOK
# ======================
with tab3:
    st.header("\U0001F4CB Status Stok Barang")
    if not st.session_state.barang:
        st.info("Belum ada barang.")
    else:
        df = pd.DataFrame(st.session_state.barang)
        kosong = df[df["stok"] == 0]
        tersedia = df[df["stok"] > 0]
        st.subheader("Barang Habis")
        if not kosong.empty:
            st.dataframe(kosong)
        else:
            st.success("Tidak ada barang habis.")

        st.subheader("Barang Tersedia")
        if not tersedia.empty:
            st.dataframe(tersedia)
        else:
            st.warning("Tidak ada barang tersedia.")

        if st.session_state.role == "admin":
            st.subheader("Edit / Hapus Barang")
            for i, b in enumerate(st.session_state.barang):
                with st.expander(f"{b['nama']}"):
                    nama_baru = st.text_input("Nama", b["nama"], key=f"nama_{i}")
                    kategori_baru = st.text_input("Kategori", b["kategori"], key=f"kat_{i}")
                    modal_baru = st.number_input("Modal", value=b["harga_modal"], key=f"mod_{i}")
                    jual_baru = st.number_input("Jual", value=b["harga_jual"], key=f"jual_{i}")
                    stok_baru = st.number_input("Stok", value=b["stok"], key=f"stok_{i}", step=1)

                    if st.button("\U0001F4BE Simpan", key=f"simpan_{i}"):
                        b.update({
                            "nama": nama_baru,
                            "kategori": kategori_baru,
                            "harga_modal": modal_baru,
                            "harga_jual": jual_baru,
                            "stok": stok_baru
                        })
                        simpan_data(BARANG_FILE, st.session_state.barang)
                        st.success("Barang diperbarui.")

                    if st.button("\U0001F5D1️ Hapus", key=f"hapus_{i}"):
                        st.session_state.barang.pop(i)
                        simpan_data(BARANG_FILE, st.session_state.barang)
                        st.rerun()

# ======================
# 📜 RIWAYAT TRANSAKSI
# ======================
with tab4:
    st.header("\U0001F9FE Riwayat Transaksi")
    df = pd.DataFrame(st.session_state.transaksi)
    if df.empty:
        st.info("Belum ada transaksi.")
    else:
        df["waktu"] = pd.to_datetime(df["waktu"])
        tanggal_mulai = st.date_input("Dari Tanggal", df["waktu"].min().date())
        tanggal_akhir = st.date_input("Sampai Tanggal", df["waktu"].max().date())
        mask = (df["waktu"].dt.date >= tanggal_mulai) & (df["waktu"].dt.date <= tanggal_akhir)
        df = df[mask]

        if st.session_state.role == "kasir":
            df = df[df["user"] == st.session_state.user]

        st.dataframe(df)

# ======================
# 📊 DASHBOARD
# ======================
with tab5:
    st.header("\U0001F4C8 Dashboard")
    df = pd.DataFrame(st.session_state.transaksi)
    if df.empty:
        st.info("Belum ada transaksi.")
    else:
        tab_a, tab_b = st.tabs(["\U0001F4CA Grafik", "\U0001F4CB Tabel"])
        with tab_a:
            fig1 = px.bar(df.groupby("nama")["jumlah"].sum().reset_index(), x="nama", y="jumlah", title="Penjualan per Barang")
            fig2 = px.pie(df, names="nama", values="keuntungan", title="Kontribusi Keuntungan")
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
        with tab_b:
            st.dataframe(df.groupby("nama")[["jumlah", "keuntungan"]].sum().reset_index())

# ======================
# 📤 EKSPOR DATA
# ======================
with tab6:
    st.header("\U0001F4E4 Ekspor Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.barang:
            df = pd.DataFrame(st.session_state.barang)
            st.download_button("⬇️ Unduh Barang", df.to_csv(index=False), file_name="barang.csv")
    with col2:
        if st.session_state.transaksi:
            df = pd.DataFrame(st.session_state.transaksi)
            st.download_button("⬇️ Unduh Transaksi", df.to_csv(index=False), file_name="transaksi.csv")
