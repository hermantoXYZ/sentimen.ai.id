# Sentimen.ai.id — Aplikasi Analisis Sentimen Bahasa Indonesia

Aplikasi analisis sentimen berbasis **Streamlit** yang dirancang untuk menganalisis teks Bahasa Indonesia menggunakan kombinasi model **IndoBERT**, **VADER**, dan **TextBlob**.

---

## ✨ Fitur Utama

- 📝 **Input Teks Manual** — Masukkan satu atau banyak teks sekaligus
- 🧹 **Cleaning Data Lengkap**:
  - Deteksi bahasa otomatis
  - Normalisasi teks (lowercase, hapus URL, mention, hashtag)
  - Hapus emoji, karakter khusus, angka
  - Hapus stopword Bahasa Indonesia
  - Stemming dengan Sastrawi
  - Hapus duplikat
- 🤖 **Analisis Sentimen Multi-Model**:
  - **IndoBERT** — Model transformer Bahasa Indonesia
  - **VADER** — Rule-based sentiment analysis
  - **TextBlob** — NLP library berbasis leksikon
  - **Ensemble** — Kombinasi ketiga model
- 📊 **Visualisasi Interaktif**:
  - Pie chart distribusi sentimen
  - Bar chart perbandingan model
  - Word Cloud per kategori sentimen
  - Tabel hasil lengkap dengan skor

---

## 🚀 Cara Menjalankan

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Sentimen.ai.id.git
cd Sentimen.ai.id
```

### 2. Buat Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi
```bash
streamlit run app.py
```

---

## 📁 Struktur Project

```
Sentimen.ai.id/
├── app.py                  # Main Streamlit application
├── modules/
│   ├── __init__.py
│   ├── cleaning.py         # Data cleaning pipeline
│   ├── sentiment.py        # Sentiment analysis models
│   └── visualization.py   # Charts & visualizations
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Helper functions
├── data/
│   └── kamus_alay.json     # Kamus kata gaul/alay Indonesia
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Framework | Streamlit |
| NLP Model | IndoBERT (indobenchmark/indobert-base-p1) |
| Sentiment | VADER, TextBlob |
| Stemming | PySastrawi |
| Visualisasi | Plotly, Matplotlib, WordCloud |
| Bahasa | Python 3.10+ |

---

## 📝 Cara Penggunaan

1. Buka aplikasi di browser (`http://localhost:8501`)
2. Masukkan teks pada kolom input (satu teks per baris)
3. Pilih model yang ingin digunakan
4. Atur opsi cleaning sesuai kebutuhan
5. Klik **"Analisis Sentimen"**
6. Lihat hasil di dashboard visualisasi
7. Download hasil analisis (CSV/Excel)

---

## 📄 Lisensi

MIT License — bebas digunakan untuk keperluan pendidikan dan penelitian.
