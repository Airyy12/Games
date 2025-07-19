import sqlite3
import bcrypt
import qrcode
from fpdf import FPDF
from io import BytesIO

DB_FILE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS akun (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS barang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kategori TEXT NOT NULL,
            harga_modal REAL NOT NULL,
            harga_jual REAL NOT NULL,
            stok INTEGER NOT NULL,
            terjual INTEGER DEFAULT 0,
            stok_minimum INTEGER DEFAULT 5
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL,
            nama TEXT NOT NULL,
            kategori TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            total REAL NOT NULL,
            keuntungan REAL NOT NULL,
            user TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_pdf_struk(data, total_bayar, uang_bayar, kembalian, waktu, user):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="TOKO WAWAN", ln=True, align="C")
    pdf.cell(200, 10, txt="Jl. Contoh No.1 Telp 0812-XXXX-XXXX", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Kasir: {user} | Waktu: {waktu}", ln=True)
    pdf.ln(5)
    for item in data:
        pdf.cell(200, 10, txt=f"{item['nama']} x{item['jumlah']} @Rp{item['harga_satuan']:,}", ln=True)
        pdf.cell(200, 10, txt=f"Subtotal: Rp{item['subtotal']:,}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Total: Rp{total_bayar:,}", ln=True)
    pdf.cell(200, 10, txt=f"Bayar: Rp{uang_bayar:,} | Kembali: Rp{kembalian:,}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Terima kasih telah berbelanja", ln=True, align="C")
    qr = qrcode.make(f"Total: Rp{total_bayar:,}, Kasir: {user}, Waktu: {waktu}")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    pdf.image(buf, x=80, y=pdf.get_y(), w=50)
    buf.close()
    return pdf.output(dest="S").encode('latin-1')
