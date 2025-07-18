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
        df_barang = pd.DataFrame(st.session_state.barang)

        # ==== Langkah 1: Inisialisasi keranjang ====
        if "keranjang" not in st.session_state:
            st.session_state.keranjang = {}

        # ==== Langkah 2: Filter kategori hanya untuk tampilan ====
        kategori_unik = df_barang["kategori"].unique().tolist()
        kategori_pilih = st.selectbox("Filter Kategori:", ["Semua"] + kategori_unik)

        if kategori_pilih != "Semua":
            df_filter = df_barang[df_barang["kategori"] == kategori_pilih]
        else:
            df_filter = df_barang

        daftar_nama = df_filter["nama"].tolist()
        barang_dipilih = st.selectbox("Pilih Barang untuk Ditambahkan ke Keranjang:", [""] + daftar_nama)

        if barang_dipilih:
            if st.button("➕ Tambah ke Keranjang"):
                if barang_dipilih not in st.session_state.keranjang:
                    st.session_state.keranjang[barang_dipilih] = 1
                else:
                    st.session_state.keranjang[barang_dipilih] += 1
                st.success(f"{barang_dipilih} ditambahkan ke keranjang.")

        # ==== Langkah 3: Tampilkan isi keranjang ====
        if st.session_state.keranjang:
            st.write("### 🧺 Keranjang Belanja")
            total = 0
            qty_dict = {}
            subtotal_dict = {}

            for nama, qty in st.session_state.keranjang.items():
                barang = next(b for b in st.session_state.barang if b["nama"] == nama)
                col1, col2, col3 = st.columns([5, 3, 2])
                with col1:
                    st.write(f"**{nama}** - Rp {barang['harga_jual']:,}")
                with col2:
                    qty_input = st.number_input(f"Jumlah {nama}", min_value=1, step=1, value=qty, key=f"qty_{nama}")
                    qty_dict[nama] = qty_input
                with col3:
                    if st.button("🗑️ Hapus", key=f"del_{nama}"):
                        del st.session_state.keranjang[nama]
                        st.rerun()
                subtotal = qty_input * barang["harga_jual"]
                subtotal_dict[nama] = subtotal
                total += subtotal

            st.write("### Total Belanja")
            for nama in st.session_state.keranjang:
                st.write(f"- {nama} x {qty_dict[nama]} = Rp {subtotal_dict[nama]:,}")
            st.write(f"### 🧾 Total: Rp {total:,}")

            bayar = st.number_input("Bayar (Rp)", min_value=0, step=1000)
            if st.button("💵 Proses Pembayaran"):
                if bayar < total:
                    st.error("Uang tidak cukup.")
                else:
                    kembali = bayar - total
                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Simpan transaksi & update stok
                    for nama in st.session_state.keranjang:
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

                    st.session_state.keranjang.clear()
                    for k in list(st.session_state.keys()):
                        if k.startswith("qty_"):
                            del st.session_state[k]

                    st.success("Transaksi berhasil!")

                    # Struk
                    st.markdown("#### 🧾 Struk Pembelian")
                    st.code(f"""
Waktu: {waktu}
Total: Rp {total:,}
Bayar: Rp {bayar:,}
Kembali: Rp {kembali:,}
Barang:
""" + "\n".join([f"- {n} x {qty_dict[n]} = Rp {subtotal_dict[n]:,}" for n in qty_dict]))

        else:
            st.info("Keranjang kosong. Silakan pilih barang dari daftar.")


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
        df_barang = pd.DataFrame(st.session_state.barang)

        # ----- Grafik Barang Terjual -----
        fig1 = px.bar(
            df_trx.groupby("nama")["jumlah"].sum().reset_index(),
            x="nama", y="jumlah",
            title="Barang Terjual",
            color_discrete_sequence=["skyblue"]
        )
        st.plotly_chart(fig1, use_container_width=True)

        # ----- Grafik Keuntungan per Barang -----
        fig2 = px.pie(
            df_trx, names="nama", values="keuntungan",
            title="Kontribusi Keuntungan per Barang"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ===============================
        # 🔢 Ringkasan Keuntungan
        # ===============================
        st.subheader("📋 Ringkasan Keuntungan")

        # Keuntungan per barang
        keuntungan_barang = df_trx.groupby("nama")["keuntungan"].sum().reset_index()

        # Gabungkan dengan kategori dari data barang
        df_kategori = df_barang[["nama", "kategori"]]
        keuntungan_kategori = df_trx.merge(df_kategori, on="nama").groupby("kategori")["keuntungan"].sum().reset_index()

        total_keuntungan = df_trx["keuntungan"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Total Keuntungan", f"Rp {total_keuntungan:,.0f}")
            st.write("**Keuntungan per Barang**")
            st.dataframe(keuntungan_barang)
        with col2:
            st.write("**Keuntungan per Kategori**")
            st.dataframe(keuntungan_kategori)

        # ===============================
        # 📈 Grafik Tambahan
        # ===============================
        st.subheader("📊 Grafik Berdasarkan Kategori")

        # Penjualan per kategori
        penjualan_kategori = df_trx.merge(df_kategori, on="nama").groupby("kategori")["jumlah"].sum().reset_index()

        fig3 = px.bar(
            keuntungan_kategori, x="kategori", y="keuntungan",
            title="Keuntungan vs Kategori", color_discrete_sequence=["mediumseagreen"]
        )
        fig4 = px.bar(
            penjualan_kategori, x="kategori", y="jumlah",
            title="Penjualan vs Kategori", color_discrete_sequence=["salmon"]
        )

        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)


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
