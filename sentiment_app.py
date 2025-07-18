import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Unduh lexicon NLTK
nltk.download('vader_lexicon')

# Inisialisasi analyzer
sia = SentimentIntensityAnalyzer()

# Konfigurasi halaman
st.set_page_config(page_title="Pendeteksi Sentimen", layout="wide")

st.title("💬 Aplikasi Analisis Sentimen")
st.write("Masukkan teks atau upload file CSV untuk mendeteksi sentimen dari teks secara otomatis.")

# Pilih metode input
option = st.radio("Pilih metode input:", ("Ketik Manual", "Upload CSV"))

if option == "Ketik Manual":
    text = st.text_area("Masukkan teks di sini", height=200)
    if st.button("Analisis"):
        if text:
            score = sia.polarity_scores(text)
            st.write("**Hasil Sentimen:**")
            st.json(score)

            if score['compound'] >= 0.05:
                st.success("Sentimen Positif")
            elif score['compound'] <= -0.05:
                st.error("Sentimen Negatif")
            else:
                st.info("Sentimen Netral")
        else:
            st.warning("Silakan masukkan teks terlebih dahulu.")

else:
    uploaded_file = st.file_uploader("Upload file CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("📄 Data Awal:", df.head())

        if 'text' not in df.columns:
            st.error("Kolom 'text' tidak ditemukan dalam file CSV.")
        else:
            df['sentiment'] = df['text'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
            df['label'] = df['sentiment'].apply(
                lambda x: 'Positif' if x >= 0.05 else ('Negatif' if x <= -0.05 else 'Netral')
            )

            st.subheader("📊 Distribusi Sentimen")
            fig, ax = plt.subplots()
            sns.countplot(data=df, x='label', ax=ax, palette='viridis')
            st.pyplot(fig)

            st.subheader("☁️ Wordcloud Kata Positif & Negatif")

            pos_words = ' '.join(df[df['label'] == 'Positif']['text'].dropna())
            neg_words = ' '.join(df[df['label'] == 'Negatif']['text'].dropna())

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Wordcloud Positif**")
                wordcloud = WordCloud(width=400, height=300, background_color='white').generate(pos_words)
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

            with col2:
                st.markdown("**Wordcloud Negatif**")
                wordcloud = WordCloud(width=400, height=300, background_color='white').generate(neg_words)
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

            st.subheader("📋 Hasil Analisis:")
            st.dataframe(df[['text', 'label']])
