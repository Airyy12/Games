import streamlit as st
import json
import os

# ==== Konstanta ====
AKUN_FILE = "akun.json"

# ==== Fungsi untuk memuat dan menyimpan akun ====
def load_akun():
    if os.path.exists(AKUN_FILE):
        with open(AKUN_FILE, "r") as f:
            return json.load(f)
    else:
        akun_default = [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "kasir", "password": "kasir123", "role": "kasir"}
        ]
        save_akun(akun_default)
        return akun_default

def save_akun(data):
    with open(AKUN_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ==== Setup session state ====
if "akun" not in st.session_state:
    st.session_state.akun = load_akun()

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.user = None
    st.session_state.role = None

# ==== Halaman Login ====
st.title("🔐 Login Kasir")

menu_login = st.radio("Pilih Menu:", ["Login", "Daftar Akun"])

if menu_login == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.radio("Pilih Role:", ["admin", "kasir"])

    if st.button("Masuk"):
        akun = next((a for a in st.session_state.akun if a["username"] == username and a["password"] == password and a["role"] == role), None)
        if akun:
            st.success(f"✅ Berhasil login sebagai **{akun['role']}** ({akun['username']})")
            st.session_state.login = True
            st.session_state.user = akun["username"]
            st.session_state.role = akun["role"]
        else:
            st.error("❌ Username, password, atau role salah!")

elif menu_login == "Daftar Akun":
    st.subheader("📝 Buat Akun Baru")

    new_username = st.text_input("Username Baru")
    new_password = st.text_input("Password Baru", type="password")
    new_role = st.radio("Role:", ["admin", "kasir"], horizontal=True)

    if st.button("Buat Akun"):
        if any(a["username"] == new_username for a in st.session_state.akun):
            st.warning("⚠️ Username sudah terpakai.")
        else:
            akun_baru = {
                "username": new_username,
                "password": new_password,
                "role": new_role
            }
            st.session_state.akun.append(akun_baru)
            save_akun(st.session_state.akun)
            st.success("✅ Akun berhasil dibuat! Silakan login.")

# ==== Jika sudah login ====
if st.session_state.login:
    st.markdown("---")
    st.success(f"Selamat datang, **{st.session_state.user}** ({st.session_state.role}) 👋")

    if st.button("Logout"):
        st.session_state.login = False
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()
