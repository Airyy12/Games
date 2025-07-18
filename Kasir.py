# Aplikasi Kasir Toko dengan Streamlit
# Fitur: Login Role, Multi-item Transaksi, Struk, Riwayat, Dashboard, Ekspor CSV

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Kasir Toko", layout="wide")

# =============================
# SESSION STATE SETUP
# =============================
if "role" not in st.session_state:
    st.session_state.role = None
if "barang" not in st.session_state:
    st.session_state.barang = []
if "transaksi" not in st.session_state:
    st.session_state.transaksi = []

# =============================
# LOGIN PAGE
# =============================
if not st.session_state.role:
    st.title("🔐 Login Kasir")
    role = st.radio("Pilih Role:", ["admin", "kasir"])
    if st.button("Masuk"):
        st.session_state.role = role
        st.rerun()
else:
    st.sidebar.title("👤 Info Pengguna")
    st.sidebar.write(f"Role: **{st.session_state.role.title()}**")
    if st.sidebar.button("🔒 Logout"):
        st.session_state.role = None
        st.rerun()

# =============================
# TAB SETUP
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Input Barang", "🛒 Kasir", "🧾 Struk & Riwayat", "📈 Dashboard", "📤 Ekspor Data"
])

# =============================
# 📦 TAB 1: Input Barang
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
# 🛒 TAB 2: Kasir
# =============================
with tab2:
    st.header("🛒 Transaksi Kasir")
    if not st.session_state.barang:
        st.warning("Belum ada barang di stok.")
    else:
        df = pd.DataFrame(st.session_state.barang)
        daftar_nama = df["nama"].tolist()
        barang_dipilih = st.multiselect("Pilih Barang:", daftar_nama)

        if barang_dipilih:
            qty_dict = {}
            subtotal_dict = {}
            total = 0
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

                    # Update stok dan catat transaksi per item
                    for nama in barang_dipilih:
                        barang = next(b for b in st.session_state.barang if b["nama"] == nama)
                        jumlah = qty_dict[nama]
                        if jumlah <= barang["stok"]:
                            barang["stok"] -= jumlah
                            barang["terjual"] += jumlah
                            st.session_state.transaksi.append({
                                "waktu": waktu,
                                "nama": nama,
                                "jumlah": jumlah,
                                "total": subtotal_dict[nama],
                                "keuntungan": (barang["harga_jual"] - barang["harga_modal"]) * jumlah
                            })

                    # Tampilkan struk
                    st.success("Transaksi berhasil!")
                    st.markdown("""
                    #### 🧾 Struk Pembelian
                    """)
                    st.code(f"""
Waktu: {waktu}
Total: Rp {total:,}
Bayar: Rp {bayar:,}
Kembali: Rp {kembali:,}
Barang:
""" + "\n".join([f"- {n} x {qty_dict[n]} = Rp {subtotal_dict[n]:,}" for n in barang_dipilih]))

# =============================
# 🧾 TAB 3: Riwayat Transaksi
# =============================
with tab3:
    st.header("🧾 Riwayat Transaksi")
    if not st.session_state.transaksi:
        st.info("Belum ada transaksi.")
    else:
        df_trx = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df_trx)

# =============================
# 📈 TAB 4: Dashboard Penjualan
# =============================
with tab4:
    st.header("📈 Grafik Penjualan & Keuntungan")
    if not st.session_state.transaksi:
        st.info("Belum ada data transaksi.")
    else:
        df_trx = pd.DataFrame(st.session_state.transaksi)
        fig1 = px.bar(df_trx.groupby("nama")["jumlah"].sum().reset_index(), x="nama", y="jumlah", title="Barang Terjual")
        fig2 = px.pie(df_trx, names="nama", values="keuntungan", title="Kontribusi Keuntungan per Barang")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

# =============================
# 📤 TAB 5: Ekspor Data
# =============================
with tab5:
    st.header("📤 Ekspor CSV")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.barang:
            df_barang = pd.DataFrame(st.session_state.barang)
            st.download_button("⬇️ Unduh Data Barang", df_barang.to_csv(index=False), file_name="barang.csv")
    with col2:
        if st.session_state.transaksi:
            df_transaksi = pd.DataFrame(st.session_state.transaksi)
            st.download_button("⬇️ Unduh Riwayat Transaksi", df_transaksi.to_csv(index=False), file_name="transaksi.csv")
