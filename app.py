"""
╔═══════════════════════════════════════════════════════════════╗
║           Sentimen.ai.id — Aplikasi Analisis Sentimen         ║
║           Berbasis Streamlit untuk Bahasa Indonesia            ║
║           Model: IndoBERT + VADER + TextBlob (Ensemble)       ║
╚═══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sentimen.ai.id — Analisis Sentimen Bahasa Indonesia",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/Sentimen.ai.id',
        'Report a bug': 'https://github.com/yourusername/Sentimen.ai.id/issues',
        'About': '**Sentimen.ai.id** — Analisis sentimen teks Bahasa Indonesia menggunakan IndoBERT, VADER, dan TextBlob.'
    }
)

# ─────────────────────────────────────────────────────────────────
# CUSTOM CSS — DARK GLASSMORPHISM THEME
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Root Variables */
:root {
    --bg-primary: #050d1a;
    --bg-secondary: #0f1e35;
    --bg-card: #111827;
    --border: rgba(99,102,241,0.2);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent: #6366f1;
    --accent-glow: rgba(99,102,241,0.3);
    --positif: #22c55e;
    --negatif: #ef4444;
    --netral: #f59e0b;
}

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary);
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #050d1a 0%, #0a1628 40%, #0d1f3c 70%, #050d1a 100%);
    background-attachment: fixed;
}

/* Background grid pattern */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0f1e35 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

/* Cards / Containers */
.metric-card {
    background: linear-gradient(135deg, rgba(17,24,39,0.9), rgba(30,41,59,0.6));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(20px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.metric-card:hover {
    border-color: rgba(99,102,241,0.5);
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
    transform: translateY(-2px);
}

/* Hero Header */
.hero-header {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08));
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 24px;
    padding: 40px;
    text-align: center;
    margin-bottom: 32px;
    backdrop-filter: blur(20px);
    box-shadow: 0 0 60px rgba(99,102,241,0.1), inset 0 1px 0 rgba(255,255,255,0.05);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.05); }
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c4b5fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 12px 0;
    line-height: 1.1;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin: 0;
    font-weight: 400;
}

/* Section Headers */
.section-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 16px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Divider */
.custom-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
    margin: 28px 0;
}

/* Step Cards (Cleaning Pipeline) */
.step-card {
    background: rgba(17,24,39,0.8);
    border: 1px solid rgba(99,102,241,0.15);
    border-left: 3px solid #6366f1;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 14px;
    color: #cbd5e1;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    transition: all 0.2s ease;
}
.step-card:hover {
    border-left-color: #a78bfa;
    background: rgba(99,102,241,0.05);
}
.step-label {
    color: #818cf8;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

/* Sentiment Badges */
.badge-positif {
    background: rgba(34,197,94,0.15);
    color: #22c55e;
    border: 1px solid rgba(34,197,94,0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    display: inline-block;
}
.badge-negatif {
    background: rgba(239,68,68,0.15);
    color: #ef4444;
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    display: inline-block;
}
.badge-netral {
    background: rgba(245,158,11,0.15);
    color: #f59e0b;
    border: 1px solid rgba(245,158,11,0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    display: inline-block;
}

/* Streamlit Components Overrides */
.stTextArea textarea {
    background: rgba(17,24,39,0.9) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    padding: 16px !important;
    transition: border-color 0.3s ease !important;
}
.stTextArea textarea:focus {
    border-color: rgba(99,102,241,0.7) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3) !important;
    width: 100% !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.5) !important;
    background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Download button style */
.stDownloadButton > button {
    background: linear-gradient(135deg, rgba(17,24,39,0.9), rgba(30,41,59,0.8)) !important;
    color: #818cf8 !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
.stDownloadButton > button:hover {
    background: rgba(99,102,241,0.1) !important;
    border-color: rgba(99,102,241,0.7) !important;
}

/* Checkbox */
.stCheckbox > label {
    color: #cbd5e1 !important;
    font-size: 14px !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(17,24,39,0.9) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}

/* Metrics */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(17,24,39,0.9), rgba(30,41,59,0.6));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 14px;
    padding: 20px;
    backdrop-filter: blur(10px);
}
div[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #818cf8 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(17,24,39,0.6) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f1f5f9 !important;
    background: rgba(99,102,241,0.1) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
}

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    border-radius: 100px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(17,24,39,0.7) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

/* DataFrame table */
.stDataFrame {
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Info/warning/success/error boxes */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(15,23,42,0.5); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.7); }

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Sidebar logo/title area */
.sidebar-logo {
    text-align: center;
    padding: 20px 16px 24px;
    border-bottom: 1px solid rgba(99,102,241,0.2);
    margin-bottom: 24px;
}
.sidebar-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #c4b5fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 8px 0 4px;
}
.sidebar-sub {
    color: #64748b;
    font-size: 12px;
}

/* Results table */
.result-row {
    background: rgba(17,24,39,0.6);
    border: 1px solid rgba(99,102,241,0.1);
    border-radius: 10px;
    padding: 16px;
    margin: 8px 0;
    transition: all 0.2s ease;
}
.result-row:hover {
    border-color: rgba(99,102,241,0.3);
    background: rgba(99,102,241,0.05);
}

/* Animated gradient text */
.gradient-text {
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c4b5fd, #818cf8);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradient-shift 3s linear infinite;
}
@keyframes gradient-shift {
    to { background-position: 200% center; }
}

/* Info panel */
.info-panel {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 14px;
    padding: 20px;
    margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# IMPORTS MODULES
# ─────────────────────────────────────────────────────────────────
from modules.cleaning import TextCleaner
from modules.sentiment import (
    analyze_text_full, analyze_batch, load_indobert,
    VADER_AVAILABLE, TEXTBLOB_AVAILABLE, SENTIMENT_COLORS, SENTIMENT_EMOJIS
)
from modules.visualization import (
    create_pie_chart, create_bar_chart, create_confidence_chart,
    create_wordcloud, create_wordclouds_by_sentiment, create_heatmap
)
from utils.helpers import (
    dataframe_to_csv_bytes, dataframe_to_excel_bytes,
    parse_text_input, get_sentiment_badge_html,
    format_confidence, create_metric_card_html, get_sample_texts
)

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
if 'cleaned_df' not in st.session_state:
    st.session_state.cleaned_df = None
if 'sentiment_df' not in st.session_state:
    st.session_state.sentiment_df = None
if 'indobert_loaded' not in st.session_state:
    st.session_state.indobert_loaded = False
if 'raw_texts' not in st.session_state:
    st.session_state.raw_texts = []


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div style="font-size: 2.5rem;">🧠</div>
        <div class="sidebar-title">Sentimen.ai.id</div>
        <div class="sidebar-sub">Analisis Sentimen Bahasa Indonesia</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── SECTION: Model AI ───
    st.markdown("### 🤖 Model AI")

    col1, col2 = st.columns(2)
    with col1:
        use_vader = st.checkbox("VADER", value=True, key="use_vader",
                                help="Rule-based model, cepat dan efektif untuk teks pendek")
        use_textblob = st.checkbox("TextBlob", value=True, key="use_textblob",
                                   help="NLP library berbasis leksikon")
    with col2:
        use_indobert = st.checkbox("IndoBERT", value=False, key="use_indobert",
                                   help="Model transformer BERT untuk Bahasa Indonesia (memerlukan download ~500MB)")

    if use_indobert and not st.session_state.indobert_loaded:
        if st.button("⬇️ Load IndoBERT Model", key="load_indobert"):
            with st.spinner("Memuat model IndoBERT... (pertama kali ~500MB)"):
                success = load_indobert()
                if success:
                    st.session_state.indobert_loaded = True
                    st.success("✅ IndoBERT berhasil dimuat!")
                else:
                    st.error("❌ Gagal memuat IndoBERT. Cek koneksi internet.")

    elif st.session_state.indobert_loaded:
        st.success("✅ IndoBERT aktif")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ─── SECTION: Cleaning Options ───
    st.markdown("### 🧹 Opsi Cleaning")

    cleaning_config = {
        'detect_language': st.checkbox("Deteksi Bahasa", value=True, key="det_lang"),
        'lowercase': st.checkbox("Lowercase", value=True, key="lowercase"),
        'remove_html': st.checkbox("Hapus HTML Tags", value=True, key="rm_html"),
        'fix_encoding': st.checkbox("Fix Encoding", value=True, key="fix_enc"),
        'remove_urls': st.checkbox("Hapus URL", value=True, key="rm_urls"),
        'remove_mentions': st.checkbox("Hapus Mention (@)", value=True, key="rm_mention"),
        'remove_hashtags': st.checkbox("Hapus Hashtag (#)", value=True, key="rm_hashtag"),
        'remove_emojis': st.checkbox("Hapus Emoji", value=True, key="rm_emoji"),
        'normalize_alay': st.checkbox("Normalisasi Kata Alay", value=True, key="norm_alay"),
        'normalize_repeated': st.checkbox("Normalisasi Karakter Berulang", value=True, key="norm_rep"),
        'remove_special_chars': st.checkbox("Hapus Karakter Khusus", value=True, key="rm_spec"),
        'remove_numbers': st.checkbox("Hapus Angka", value=True, key="rm_num"),
        'remove_stopwords': st.checkbox("Hapus Stopwords", value=True, key="rm_stop"),
        'stemming': st.checkbox("Stemming (Sastrawi)", value=False, key="stemming",
                                help="⚠️ Stemming mengubah kata ke bentuk dasar, bisa mempengaruhi akurasi sentimen"),
        'remove_duplicates': st.checkbox("Hapus Duplikat", value=True, key="rm_dup"),
        'min_length': 3,
    }

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ─── SECTION: Tentang ───
    st.markdown("### ℹ️ Tentang")
    st.markdown("""
    <div class="info-panel" style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
        <b style="color: #818cf8;">Sentimen.ai.id</b> adalah platform analisis sentimen 
        teks Bahasa Indonesia menggunakan model AI mutakhir.<br><br>
        📌 <b>Stack:</b> Streamlit, IndoBERT, VADER, TextBlob, Sastrawi<br>
        🔢 <b>Versi:</b> 1.0.0<br>
        📄 <b>Lisensi:</b> MIT
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────

# Hero Header
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🧠 Sentimen.ai.id</div>
    <p class="hero-subtitle">
        Platform Analisis Sentimen Bahasa Indonesia Berbasis AI<br>
        <span style="color: #6366f1; font-weight: 500;">IndoBERT × VADER × TextBlob × Ensemble</span>
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TAB NAVIGATION
# ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Input & Cleaning",
    "🤖 Analisis Sentimen",
    "📊 Visualisasi",
    "📥 Download Hasil"
])


# ═══════════════════════════════════════════════════════════════
# TAB 1: INPUT & CLEANING
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-header">📝 Input Teks</p>', unsafe_allow_html=True)

    # Tombol contoh teks
    col_demo, col_clear = st.columns([2, 1])
    with col_demo:
        if st.button("💡 Muat Contoh Teks Demo", key="load_demo"):
            st.session_state['demo_texts'] = '\n'.join(get_sample_texts())
    with col_clear:
        if st.button("🗑️ Hapus Semua", key="clear_all"):
            st.session_state['demo_texts'] = ''
            st.session_state.cleaned_df = None
            st.session_state.sentiment_df = None

    # Textarea input
    default_text = st.session_state.get('demo_texts', '')
    text_input = st.text_area(
        label="Masukkan teks (satu teks per baris):",
        value=default_text,
        height=250,
        placeholder="Ketik atau tempel teks di sini...\nSatu teks per baris.\n\nContoh:\nProduk ini sangat bagus! Saya sangat puas.\nPelayanan sangat buruk, paket terlambat.",
        key="text_input",
        label_visibility="collapsed"
    )

    raw_texts = parse_text_input(text_input)

    # Statistik input
    if raw_texts:
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("📄 Total Teks", len(raw_texts))
        with col_s2:
            avg_words = np.mean([len(t.split()) for t in raw_texts])
            st.metric("📊 Rata-rata Kata", f"{avg_words:.1f}")
        with col_s3:
            total_chars = sum(len(t) for t in raw_texts)
            st.metric("🔤 Total Karakter", f"{total_chars:,}")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Tombol Cleaning
    clean_btn = st.button(
        "🧹 Jalankan Data Cleaning",
        key="run_cleaning",
        disabled=not bool(raw_texts)
    )

    if clean_btn and raw_texts:
        st.session_state.raw_texts = raw_texts

        with st.spinner("⚙️ Memproses data cleaning..."):
            cleaner = TextCleaner(config=cleaning_config)
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Process dengan progress
            results = []
            for i, text in enumerate(raw_texts):
                res = cleaner.clean_single(text, return_steps=True)
                results.append({
                    'teks_asli': res['original'],
                    'teks_bersih': res['cleaned'],
                    'bahasa': res['language'],
                    'jumlah_kata_asli': res.get('word_count_before', 0),
                    'jumlah_kata_bersih': res.get('word_count_after', 0),
                    'valid': res['is_valid'],
                    '_steps': res.get('steps', {})
                })
                progress_bar.progress((i + 1) / len(raw_texts))
                status_text.text(f"Memproses {i+1}/{len(raw_texts)} teks...")
                time.sleep(0.02)

            cleaned_df = pd.DataFrame(results)

            # Hapus duplikat jika dikonfigurasi
            n_before_dedup = len(cleaned_df)
            if cleaning_config.get('remove_duplicates', True):
                cleaned_df = cleaned_df.drop_duplicates(subset=['teks_bersih'])
            n_dedup = n_before_dedup - len(cleaned_df)

            status_text.empty()
            progress_bar.empty()
            st.session_state.cleaned_df = cleaned_df

        st.success(f"✅ Cleaning selesai! {len(cleaned_df)} teks berhasil diproses, {n_dedup} duplikat dihapus.")

    # Tampilkan hasil cleaning
    if st.session_state.cleaned_df is not None:
        df = st.session_state.cleaned_df

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">🔍 Hasil Data Cleaning</p>', unsafe_allow_html=True)

        # Stats cleaning
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Valid", int(df['valid'].sum()))
        with col2:
            st.metric("❌ Invalid", int((~df['valid']).sum()))
        with col3:
            st.metric("🗑️ Duplikat Hapus", len(st.session_state.raw_texts) - len(df))
        with col4:
            avg_reduction = ((df['jumlah_kata_asli'] - df['jumlah_kata_bersih']) / df['jumlah_kata_asli'].replace(0, 1) * 100).mean()
            st.metric("📉 Reduksi Kata", f"{avg_reduction:.1f}%")

        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

        # Pipeline Steps Viewer
        with st.expander("🔬 Lihat Detail Langkah Cleaning (contoh teks pertama)"):
            if '_steps' in df.columns and len(df) > 0:
                steps = df.iloc[0].get('_steps', {})
                original = df.iloc[0]['teks_asli']

                st.markdown(f"""
                <div class="step-card">
                    <div class="step-label">🔹 Teks Original</div>
                    {original}
                </div>
                """, unsafe_allow_html=True)

                step_names = {
                    'fix_encoding': 'Fix Encoding',
                    'remove_html': 'Hapus HTML Tags',
                    'lowercase': 'Lowercase',
                    'remove_urls': 'Hapus URL',
                    'remove_mentions': 'Hapus Mention',
                    'remove_hashtags': 'Hapus Hashtag',
                    'remove_emojis': 'Hapus Emoji',
                    'normalize_alay': 'Normalisasi Alay',
                    'normalize_repeated': 'Normalisasi Berulang',
                    'remove_special_chars': 'Hapus Karakter Khusus',
                    'remove_numbers': 'Hapus Angka',
                    'remove_stopwords': 'Hapus Stopwords',
                    'stemming': 'Stemming Sastrawi',
                }

                for step_key, step_label in step_names.items():
                    if step_key in steps:
                        value = steps[step_key]
                        st.markdown(f"""
                        <div class="step-card">
                            <div class="step-label">→ {step_label}</div>
                            {value if value else '<em style="color:#475569;">kosong</em>'}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="step-card" style="border-left-color: #22c55e;">
                    <div class="step-label" style="color: #22c55e;">✅ Hasil Akhir</div>
                    {df.iloc[0]['teks_bersih'] if df.iloc[0]['teks_bersih'] else '<em>kosong</em>'}
                </div>
                """, unsafe_allow_html=True)

        # Tabel hasil cleaning
        st.markdown("**📋 Tabel Hasil Cleaning**")
        display_df = df[['teks_asli', 'teks_bersih', 'bahasa', 'jumlah_kata_asli', 'jumlah_kata_bersih', 'valid']].copy()
        display_df.columns = ['Teks Asli', 'Teks Bersih', 'Bahasa', 'Kata (Asli)', 'Kata (Bersih)', 'Valid']
        st.dataframe(
            display_df,
            use_container_width=True,
            height=350,
            column_config={
                'Valid': st.column_config.CheckboxColumn('Valid'),
                'Teks Asli': st.column_config.TextColumn('Teks Asli', max_chars=80),
                'Teks Bersih': st.column_config.TextColumn('Teks Bersih', max_chars=80),
            }
        )

        st.info("✅ Data cleaning selesai! Lanjutkan ke tab **🤖 Analisis Sentimen**.")


# ═══════════════════════════════════════════════════════════════
# TAB 2: ANALISIS SENTIMEN
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">🤖 Analisis Sentimen</p>', unsafe_allow_html=True)

    if st.session_state.cleaned_df is None:
        st.markdown("""
        <div class="info-panel" style="text-align: center; padding: 40px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">⚠️</div>
            <p style="color: #94a3b8; font-size: 1rem;">Belum ada data yang diproses.<br>
            Silakan masukkan teks dan jalankan <b>Data Cleaning</b> di tab pertama terlebih dahulu.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = st.session_state.cleaned_df
        valid_df = df[df['valid'] == True].copy()
        valid_texts = valid_df['teks_bersih'].tolist()

        # Model info
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            status = "✅ Aktif" if VADER_AVAILABLE and use_vader else "⭕ Nonaktif"
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
                <p style="font-size: 1.5rem; margin: 0;">⚡</p>
                <p style="color: #818cf8; font-weight: 700; margin: 4px 0;">VADER</p>
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">Rule-based</p>
                <p style="margin: 8px 0 0; font-size: 13px;">{status}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_info2:
            status2 = "✅ Aktif" if TEXTBLOB_AVAILABLE and use_textblob else "⭕ Nonaktif"
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
                <p style="font-size: 1.5rem; margin: 0;">📚</p>
                <p style="color: #818cf8; font-weight: 700; margin: 4px 0;">TextBlob</p>
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">Lexicon-based</p>
                <p style="margin: 8px 0 0; font-size: 13px;">{status2}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_info3:
            status3 = "✅ Aktif" if st.session_state.indobert_loaded and use_indobert else "⭕ Nonaktif"
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
                <p style="font-size: 1.5rem; margin: 0;">🧠</p>
                <p style="color: #818cf8; font-weight: 700; margin: 4px 0;">IndoBERT</p>
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">Transformer</p>
                <p style="margin: 8px 0 0; font-size: 13px;">{status3}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

        # Tombol analisis
        analyze_btn = st.button(
            "🚀 Mulai Analisis Sentimen",
            key="run_analysis",
            disabled=len(valid_texts) == 0
        )

        if analyze_btn and valid_texts:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def progress_callback(progress, message):
                progress_bar.progress(progress)
                status_text.text(message)

            with st.spinner("🔄 Menganalisis sentimen..."):
                sentiment_df = analyze_batch(
                    texts=valid_texts,
                    use_vader=use_vader,
                    use_textblob=use_textblob,
                    use_indobert=use_indobert and st.session_state.indobert_loaded,
                    progress_callback=progress_callback
                )

            progress_bar.empty()
            status_text.empty()

            # Gabungkan dengan data cleaning
            valid_df_reset = valid_df.reset_index(drop=True)
            sentiment_df = sentiment_df.reset_index(drop=True)
            merged = pd.concat([
                valid_df_reset[['teks_asli', 'teks_bersih', 'bahasa']],
                sentiment_df.drop(columns=['teks'], errors='ignore')
            ], axis=1)

            st.session_state.sentiment_df = merged
            st.success(f"✅ Analisis selesai! {len(merged)} teks berhasil dianalisis.")

        # Tampilkan hasil
        if st.session_state.sentiment_df is not None:
            sdf = st.session_state.sentiment_df

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # Summary metrics
            st.markdown('<p class="section-header">📊 Ringkasan Hasil</p>', unsafe_allow_html=True)

            if 'label_ensemble' in sdf.columns:
                total = len(sdf)
                positif = (sdf['label_ensemble'] == 'Positif').sum()
                negatif = (sdf['label_ensemble'] == 'Negatif').sum()
                netral = (sdf['label_ensemble'] == 'Netral').sum()
                avg_conf = sdf.get('confidence_ensemble', pd.Series([0])).mean()

                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("📄 Total", total)
                with col2:
                    st.metric("😊 Positif", f"{positif} ({positif/total*100:.0f}%)")
                with col3:
                    st.metric("😢 Negatif", f"{negatif} ({negatif/total*100:.0f}%)")
                with col4:
                    st.metric("😐 Netral", f"{netral} ({netral/total*100:.0f}%)")
                with col5:
                    st.metric("🎯 Avg Confidence", f"{avg_conf*100:.1f}%")

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # Detail hasil per teks
            st.markdown('<p class="section-header">📋 Detail Hasil Per Teks</p>', unsafe_allow_html=True)

            # Filter
            col_filter1, col_filter2 = st.columns([1, 2])
            with col_filter1:
                filter_sentiment = st.selectbox(
                    "Filter Sentimen:",
                    options=['Semua', 'Positif', 'Negatif', 'Netral'],
                    key="filter_sentiment"
                )

            filtered_sdf = sdf.copy()
            if filter_sentiment != 'Semua' and 'label_ensemble' in filtered_sdf.columns:
                filtered_sdf = filtered_sdf[filtered_sdf['label_ensemble'] == filter_sentiment]

            # Tampilkan tabel
            cols_to_show = ['teks_asli', 'teks_bersih']
            if 'label_vader' in filtered_sdf.columns: cols_to_show.append('label_vader')
            if 'label_textblob' in filtered_sdf.columns: cols_to_show.append('label_textblob')
            if 'label_indobert' in filtered_sdf.columns: cols_to_show.append('label_indobert')
            if 'label_ensemble' in filtered_sdf.columns: cols_to_show.append('label_ensemble')
            if 'confidence_ensemble' in filtered_sdf.columns: cols_to_show.append('confidence_ensemble')

            display = filtered_sdf[cols_to_show].copy()

            # Rename columns
            rename_map = {
                'teks_asli': 'Teks Asli',
                'teks_bersih': 'Teks Bersih',
                'label_vader': 'VADER',
                'label_textblob': 'TextBlob',
                'label_indobert': 'IndoBERT',
                'label_ensemble': 'Ensemble',
                'confidence_ensemble': 'Confidence'
            }
            display = display.rename(columns={k: v for k, v in rename_map.items() if k in display.columns})

            column_config = {
                'Teks Asli': st.column_config.TextColumn('Teks Asli', max_chars=60),
                'Teks Bersih': st.column_config.TextColumn('Teks Bersih', max_chars=60),
                'Confidence': st.column_config.ProgressColumn(
                    'Confidence',
                    min_value=0,
                    max_value=1,
                    format="%.2f"
                )
            }

            st.dataframe(display, use_container_width=True, height=400, column_config=column_config)

            st.info("✅ Analisis selesai! Lihat visualisasi di tab **📊 Visualisasi**.")


# ═══════════════════════════════════════════════════════════════
# TAB 3: VISUALISASI
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">📊 Visualisasi Hasil</p>', unsafe_allow_html=True)

    if st.session_state.sentiment_df is None:
        st.markdown("""
        <div class="info-panel" style="text-align: center; padding: 40px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">📊</div>
            <p style="color: #94a3b8;">Jalankan analisis sentimen terlebih dahulu untuk melihat visualisasi.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        sdf = st.session_state.sentiment_df

        # ── Row 1: Pie Chart + Bar Chart ──
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = create_pie_chart(sdf, 'label_ensemble', "Distribusi Sentimen (Ensemble)")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            fig_bar = create_bar_chart(sdf)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # ── Row 2: Confidence Chart + Heatmap ──
        col3, col4 = st.columns(2)
        with col3:
            fig_conf = create_confidence_chart(sdf)
            st.plotly_chart(fig_conf, use_container_width=True)

        with col4:
            fig_heat = create_heatmap(sdf)
            if fig_heat.data:
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Heatmap memerlukan minimal 2 model aktif.")

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # ── Row 3: Word Clouds ──
        st.markdown('<p class="section-header">☁️ Word Cloud per Sentimen</p>', unsafe_allow_html=True)

        text_col = 'teks_bersih' if 'teks_bersih' in sdf.columns else 'teks'
        if text_col in sdf.columns and 'label_ensemble' in sdf.columns:
            wc_figs = create_wordclouds_by_sentiment(sdf, text_col=text_col, label_col='label_ensemble')

            if wc_figs:
                wc_tabs = st.tabs([f"{k} ({len(sdf[sdf['label_ensemble']==k])} teks)" for k in wc_figs.keys()])
                for tab_wc, (sentiment, fig_wc) in zip(wc_tabs, wc_figs.items()):
                    with tab_wc:
                        st.pyplot(fig_wc, use_container_width=True)
            else:
                st.warning("Tidak cukup teks untuk membuat Word Cloud.")

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # ── Row 4: Model Comparison Pie per model ──
        st.markdown('<p class="section-header">🔍 Distribusi per Model</p>', unsafe_allow_html=True)
        model_cols = {
            'VADER': 'label_vader',
            'TextBlob': 'label_textblob',
            'IndoBERT': 'label_indobert',
        }
        available_models = {k: v for k, v in model_cols.items() if v in sdf.columns}

        if available_models:
            model_tab_names = list(available_models.keys())
            model_tabs = st.tabs(model_tab_names)
            for tab_m, (model_name, col) in zip(model_tabs, available_models.items()):
                with tab_m:
                    fig_m = create_pie_chart(sdf, col, f"Distribusi Sentimen — {model_name}")
                    st.plotly_chart(fig_m, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4: DOWNLOAD HASIL
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-header">📥 Download Hasil</p>', unsafe_allow_html=True)

    if st.session_state.sentiment_df is None and st.session_state.cleaned_df is None:
        st.markdown("""
        <div class="info-panel" style="text-align: center; padding: 40px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">📥</div>
            <p style="color: #94a3b8;">Belum ada hasil untuk diunduh.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 📂 Pilih Data yang Akan Diunduh")

        col1, col2 = st.columns(2)

        # Download Cleaning Results
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3 style="color: #818cf8; margin: 0 0 12px 0;">🧹 Hasil Cleaning</h3>
                <p style="color: #94a3b8; font-size: 13px; margin: 0 0 16px 0;">
                    Teks asli vs teks bersih, statistik kata, deteksi bahasa, dan validitas teks.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.cleaned_df is not None:
                clean_df_download = st.session_state.cleaned_df.drop(columns=['_steps'], errors='ignore')

                col_csv1, col_xlsx1 = st.columns(2)
                with col_csv1:
                    st.download_button(
                        "⬇️ Download CSV",
                        data=dataframe_to_csv_bytes(clean_df_download),
                        file_name="hasil_cleaning.csv",
                        mime="text/csv",
                        key="dl_clean_csv",
                        use_container_width=True
                    )
                with col_xlsx1:
                    st.download_button(
                        "⬇️ Download Excel",
                        data=dataframe_to_excel_bytes(clean_df_download),
                        file_name="hasil_cleaning.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_clean_xlsx",
                        use_container_width=True
                    )
            else:
                st.info("Jalankan cleaning terlebih dahulu.")

        # Download Sentiment Results
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3 style="color: #818cf8; margin: 0 0 12px 0;">🤖 Hasil Sentimen</h3>
                <p style="color: #94a3b8; font-size: 13px; margin: 0 0 16px 0;">
                    Label sentimen dari VADER, TextBlob, IndoBERT, Ensemble, dan confidence score.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.sentiment_df is not None:
                col_csv2, col_xlsx2 = st.columns(2)
                with col_csv2:
                    st.download_button(
                        "⬇️ Download CSV",
                        data=dataframe_to_csv_bytes(st.session_state.sentiment_df),
                        file_name="hasil_sentimen.csv",
                        mime="text/csv",
                        key="dl_sent_csv",
                        use_container_width=True
                    )
                with col_xlsx2:
                    st.download_button(
                        "⬇️ Download Excel",
                        data=dataframe_to_excel_bytes(st.session_state.sentiment_df),
                        file_name="hasil_sentimen.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_sent_xlsx",
                        use_container_width=True
                    )
            else:
                st.info("Jalankan analisis sentimen terlebih dahulu.")

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # Preview data
        if st.session_state.sentiment_df is not None:
            st.markdown("### 👁️ Preview Data Lengkap")
            st.dataframe(st.session_state.sentiment_df, use_container_width=True, height=400)

        st.markdown("""
        <div class="info-panel" style="margin-top: 24px;">
            <p style="color: #94a3b8; font-size: 13px; margin: 0; line-height: 1.7;">
                📌 <b style="color: #818cf8;">Format CSV</b> — cocok untuk dibuka di Excel, Google Sheets, atau diproses dengan Python/R.<br>
                📌 <b style="color: #818cf8;">Format Excel</b> — langsung bisa digunakan untuk pelaporan dan visualisasi lebih lanjut.<br>
                📌 Data menggunakan encoding <b>UTF-8-BOM</b> agar karakter Indonesia terbaca dengan benar di Excel.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 32px 0 16px; margin-top: 40px; border-top: 1px solid rgba(99,102,241,0.15);">
    <p style="color: #334155; font-size: 13px; margin: 0;">
        🧠 <b style="color: #6366f1;">Sentimen.ai.id</b> — Platform Analisis Sentimen Bahasa Indonesia &nbsp;|&nbsp; 
        Powered by <b>IndoBERT × VADER × TextBlob</b> &nbsp;|&nbsp; 
        Built with ❤️ using Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
