import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime
import plotly.express as px
import io

# Konstanta file
AKUN_FILE = "akun.json"
BARANG_FILE = "barang.json"
TRANSAKSI_FILE = "transaksi.json"
KATEGORI_FILE = "kategori.json"

# Setup halaman
st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

# ===== FUNGSI ===== #
def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return []

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_kategori():
    if not os.path.exists(KATEGORI_FILE):
        save_data(KATEGORI_FILE, [])
    return load_data(KATEGORI_FILE)

# ===== AUTENTIKASI ===== #
akun_data = load_data(AKUN_FILE)
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Login Kasir")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        for akun in akun_data:
            if akun['username'] == username and akun['password'] == hash_password(password):
                st.session_state.user = akun
                st.success("Login berhasil!")
                st.experimental_rerun()
        st.error("Username atau password salah.")
    st.stop()

# ===== MENU ===== #
menu = st.sidebar.radio("Menu", ["Transaksi", "Tambah Barang", "Riwayat Transaksi", "Laporan Keuangan", "Manajemen Kategori"])
barang_data = load_data(BARANG_FILE)
transaksi_data = load_data(TRANSAKSI_FILE)

# ===== MENU: TRANSAKSI ===== #
if menu == "Transaksi":
    st.title("🛒 Transaksi Penjualan")
    keranjang = []
    kategori_data = load_kategori()
    barang_nama = [f"{b['nama']} ({b['kategori']})" for b in barang_data if b['stok'] > 0]

    st.subheader("Tambah ke Keranjang")
    pilih_barang = st.selectbox("Pilih Barang", barang_nama)
    jumlah = st.number_input("Jumlah", 1, 100, 1)

    if st.button("➕ Tambah"):
        nama, kategori = pilih_barang.split(" (")
        kategori = kategori.rstrip(")")
        for b in barang_data:
            if b['nama'] == nama and b['kategori'] == kategori:
                if b['stok'] < jumlah:
                    st.error("Stok tidak mencukupi!")
                else:
                    keranjang.append({"nama": nama, "kategori": kategori, "jumlah": jumlah, "harga": b['harga']})

    if keranjang:
        st.subheader("🧺 Keranjang")
        total_bayar = sum(i['jumlah'] * i['harga'] for i in keranjang)
        st.table(pd.DataFrame(keranjang))
        diskon_rp = st.number_input("Diskon (Rp)", 0, total_bayar, 0)
        total_akhir = total_bayar - diskon_rp
        uang_bayar = st.number_input("Uang Dibayar", 0)

        if uang_bayar >= total_akhir and st.button("✅ Proses Transaksi"):
            id_nota = "INV" + datetime.now().strftime("%Y%m%d%H%M%S")
            transaksi_baru = {
                "id_nota": id_nota,
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": st.session_state.user['username'],
                "diskon": diskon_rp,
                "total": total_akhir,
                "detail": []
            }
            for item in keranjang:
                transaksi_baru["detail"].append({
                    "nama": item["nama"],
                    "kategori": item["kategori"],
                    "jumlah": item["jumlah"],
                    "harga": item["harga"],
                    "subtotal": item["jumlah"] * item["harga"]
                })
                for b in barang_data:
                    if b["nama"] == item["nama"] and b["kategori"] == item["kategori"]:
                        b["stok"] -= item["jumlah"]

            transaksi_data.append(transaksi_baru)
            save_data(TRANSAKSI_FILE, transaksi_data)
            save_data(BARANG_FILE, barang_data)

            kembalian = uang_bayar - total_akhir
            st.success(f"Transaksi berhasil. Kembalian: Rp {kembalian:,}")

            st.subheader("🧾 Struk Nota")
            st.write(f"Nota: {id_nota}")
            st.write(f"Tanggal: {transaksi_baru['waktu']}")
            st.write(f"Kasir: {transaksi_baru['user']}")
            for item in transaksi_baru["detail"]:
                st.write(f"- {item['nama']} ({item['jumlah']} x {item['harga']:,}) = Rp {item['subtotal']:,}")
            st.write(f"Diskon: Rp {diskon_rp:,}")
            st.write(f"Total: Rp {total_akhir:,}")
            st.write(f"Bayar: Rp {uang_bayar:,}")
            st.write(f"Kembalian: Rp {kembalian:,}")

# ===== MENU: TAMBAH BARANG ===== #
elif menu == "Tambah Barang":
    st.title("📦 Tambah Barang")
    kategori_data = load_kategori()
    nama = st.text_input("Nama Barang")
    kategori = st.selectbox("Kategori", kategori_data)
    harga = st.number_input("Harga", 0)
    stok = st.number_input("Stok", 0)

    if st.button("💾 Simpan Barang"):
        for b in barang_data:
            if b['nama'] == nama and b['kategori'] == kategori:
                b['harga'] = harga
                b['stok'] += stok
                break
        else:
            barang_data.append({"nama": nama, "kategori": kategori, "harga": harga, "stok": stok})
        save_data(BARANG_FILE, barang_data)
        st.success("Barang berhasil disimpan atau diperbarui.")

# ===== MENU: MANAJEMEN KATEGORI ===== #
elif menu == "Manajemen Kategori":
    st.title("📂 Manajemen Kategori")
    kategori_data = load_kategori()
    st.subheader("Daftar Kategori")
    st.table(pd.DataFrame(kategori_data, columns=["Kategori"]))

    new_kat = st.text_input("Tambah Kategori Baru")
    if st.button("Tambah"):
        if new_kat and new_kat not in kategori_data:
            kategori_data.append(new_kat)
            save_data(KATEGORI_FILE, kategori_data)
            st.success("Kategori ditambahkan.")

    hapus_kat = st.selectbox("Hapus Kategori", kategori_data)
    if st.button("Hapus"):
        kategori_data.remove(hapus_kat)
        save_data(KATEGORI_FILE, kategori_data)
        st.success("Kategori dihapus.")

# ===== MENU: RIWAYAT ===== #
elif menu == "Riwayat Transaksi":
    st.title("📜 Riwayat Transaksi")
    if transaksi_data:
        st.dataframe(pd.DataFrame(transaksi_data))
    else:
        st.info("Belum ada transaksi.")

# ===== MENU: LAPORAN ===== #
elif menu == "Laporan Keuangan":
    st.title("📈 Laporan Keuangan")
    rows = []
    for trx in transaksi_data:
        for item in trx["detail"]:
            rows.append({
                "Waktu": trx["waktu"],
                "Nota": trx["id_nota"],
                "User": trx["user"],
                "Kategori": item["kategori"],
                "Barang": item["nama"],
                "Jumlah": item["jumlah"],
                "Harga": item["harga"],
                "Subtotal": item["subtotal"],
                "Diskon": trx["diskon"] / len(trx["detail"]),
                "Total_Bersih": item["subtotal"] - (trx["diskon"] / len(trx["detail"]))
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Waktu"] = pd.to_datetime(df["Waktu"])
        tgl_mulai = st.date_input("Dari", df["Waktu"].min().date())
        tgl_akhir = st.date_input("Sampai", df["Waktu"].max().date())
        df = df[(df["Waktu"].dt.date >= tgl_mulai) & (df["Waktu"].dt.date <= tgl_akhir)]

        user_filter = st.multiselect("Kasir", df["User"].unique(), default=list(df["User"].unique()))
        kategori_filter = st.multiselect("Kategori", df["Kategori"].unique(), default=list(df["Kategori"].unique()))
        df = df[df["User"].isin(user_filter) & df["Kategori"].isin(kategori_filter)]

        st.metric("Total Penjualan", f"Rp {df['Subtotal'].sum():,.0f}")
        st.metric("Total Diskon", f"Rp {df['Diskon'].sum():,.0f}")
        st.metric("Total Bersih", f"Rp {df['Total_Bersih'].sum():,.0f}")

        st.subheader("📊 Grafik Harian")
        df_grafik = df.groupby(df["Waktu"].dt.date)["Total_Bersih"].sum().reset_index()
        fig = px.line(df_grafik, x="Waktu", y="Total_Bersih", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        with io.BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Laporan")
            st.download_button("⬇️ Download Excel", buffer.getvalue(), file_name="laporan_keuangan.xlsx")
    else:
        st.info("Belum ada data.")
