# Aplikasi Kasir Streamlit Lengkap

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")

# File akun disimpan permanen
AKUN_FILE = "akun.json"

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
    st.title("🔐 Login Kasir")
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

# Login
if "login" not in st.session_state:
    st.session_state.login = False
if not st.session_state.login:
    tampilkan_login()
    st.stop()

# Setup awal
if "barang" not in st.session_state:
    st.session_state.barang = []
if "transaksi" not in st.session_state:
    st.session_state.transaksi = []

st.sidebar.title("👤 Pengguna")
st.sidebar.write(f"Login sebagai: **{st.session_state.user}** ({st.session_state.role})")
if st.sidebar.button("🔒 Logout"):
    st.session_state.clear()
    st.rerun()

# Tab utama
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📦 Input Barang", "🛒 Kasir", "📋 Status Stok Barang", "🧾 Riwayat", "📈 Dashboard", "📤 Ekspor"
])

# ======================
# TAB 1: Input Barang (admin)
# ======================
with tab1:
    st.header("📦 Input Barang")
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
                st.success(f"Barang '{nama}' disimpan.")

        if st.session_state.barang:
            st.subheader("📋 Daftar Barang")
            st.dataframe(pd.DataFrame(st.session_state.barang))

# ======================
# TAB 2: Transaksi Kasir
# ======================
with tab2:
    st.header("🛒 Transaksi Kasir")
    if not st.session_state.barang:
        st.warning("Belum ada barang di stok.")
    else:
        df_all = pd.DataFrame(st.session_state.barang)
        kategori_unik = df_all["kategori"].unique().tolist()

        st.subheader("📂 Filter Kategori")
        kategori_pilih = st.selectbox("Pilih Kategori:", ["Semua"] + kategori_unik)
        df_filtered = df_all if kategori_pilih == "Semua" else df_all[df_all["kategori"] == kategori_pilih]

        st.markdown("## 📋 Daftar Barang untuk Transaksi")

        qty_dict = {}
        subtotal_dict = {}
        total = 0
        barang_dibeli = []

        for idx, b in enumerate(df_filtered.to_dict("records")):
            nama = b["nama"]
            stok = b["stok"]
            harga_jual = b["harga_jual"]

            if stok <= 0:
                continue  # skip jika stok habis

            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"**{nama}** (Stok: {stok}) - Rp {harga_jual:,}")
            with col2:
                qty = st.number_input(
                    f"Jumlah untuk '{nama}'", min_value=0, max_value=stok,
                    step=1, key=f"qty_{nama}"
                )
            with col3:
                if st.button("🗑️ Hapus", key=f"hapus_{nama}"):
                    st.session_state[f"qty_{nama}"] = 0

            if qty > 0:
                qty_dict[nama] = qty
                subtotal = qty * harga_jual
                subtotal_dict[nama] = subtotal
                total += subtotal
                barang_dibeli.append((nama, qty, subtotal))

        # ========================
        # RINGKASAN
        # ========================
        if barang_dibeli:
            st.markdown("---")
            st.markdown("## 🧾 Ringkasan")
            for nama, qty, subtotal in barang_dibeli:
                st.write(f"- {nama} x {qty} = Rp{subtotal:,}")
            st.markdown(f"### 💰 **Total Bayar: Rp{total:,}**")

            bayar = st.number_input("💵 Uang Diterima", min_value=0, step=1000)
            if st.button("✅ Proses Pembayaran"):
                if bayar < total:
                    st.error("Uang tidak cukup.")
                else:
                    kembali = bayar - total
                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    for nama, qty, subtotal in barang_dibeli:
                        barang = next(b for b in st.session_state.barang if b["nama"] == nama)
                        barang["stok"] -= qty
                        barang["terjual"] += qty
                        st.session_state.transaksi.append({
                            "waktu": waktu,
                            "nama": nama,
                            "kategori": barang["kategori"],
                            "jumlah": qty,
                            "total": subtotal,
                            "keuntungan": (barang["harga_jual"] - barang["harga_modal"]) * qty
                        })

                    # Reset qty input
                    for nama in qty_dict.keys():
                        st.session_state[f"qty_{nama}"] = 0

                    st.success("✅ Transaksi berhasil!")
                    st.code(f"""
Waktu: {waktu}
Total: Rp{total:,}
Bayar: Rp{bayar:,}
Kembali: Rp{kembali:,}
Barang:
""" + "\n".join([f"- {n} x {qty_dict[n]} = Rp{subtotal_dict[n]:,}" for n in qty_dict]))


# ======================
# TAB 3: Status Stok
# ======================
with tab3:
    st.header("📋 Status Stok Barang")
    if not st.session_state.barang:
        st.info("Belum ada barang.")
    else:
        df = pd.DataFrame(st.session_state.barang)
        kosong = df[df["stok"] == 0]
        tersedia = df[df["stok"] > 0]

        st.subheader("Barang Habis")
        if kosong.empty:
            st.success("Tidak ada barang yang habis.")
        else:
            st.dataframe(kosong)

        st.subheader("Barang Masih Tersedia")
        st.dataframe(tersedia)

# ======================
# TAB 4: Riwayat
# ======================
with tab4:
    st.header("🧾 Riwayat Transaksi")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df)

# ======================
# TAB 5: Dashboard
# ======================
with tab5:
    st.header("📈 Dashboard")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df = pd.DataFrame(st.session_state.transaksi)

        tab_a, tab_b = st.tabs(["📊 Grafik", "📋 Tabel"])
        with tab_a:
            fig1 = px.bar(df.groupby("nama")["jumlah"].sum().reset_index(), x="nama", y="jumlah", title="Penjualan per Barang")
            fig2 = px.pie(df, names="nama", values="keuntungan", title="Kontribusi Keuntungan")
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)

        with tab_b:
            st.dataframe(df.groupby("nama")[["jumlah", "keuntungan"]].sum().reset_index())

# ======================
# TAB 6: Ekspor Data
# ======================
with tab6:
    st.header("📤 Ekspor Data")
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.barang:
            df = pd.DataFrame(st.session_state.barang)
            st.download_button("⬇️ Unduh Barang", df.to_csv(index=False), file_name="barang.csv")

    with col2:
        if st.session_state.transaksi:
            df = pd.DataFrame(st.session_state.transaksi)
            st.download_button("⬇️ Unduh Transaksi", df.to_csv(index=False), file_name="transaksi.csv")
