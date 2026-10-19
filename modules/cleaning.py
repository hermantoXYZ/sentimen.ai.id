"""
Modul Cleaning Data untuk Sentimen.ai.id
Berisi pipeline pembersihan teks Bahasa Indonesia lengkap
"""

import re
import json
import os
import unicodedata
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

# NLTK imports
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Sastrawi untuk stemming Bahasa Indonesia
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    SASTRAWI_AVAILABLE = True
except ImportError:
    SASTRAWI_AVAILABLE = False

# Langdetect untuk deteksi bahasa
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Load kamus alay
KAMUS_ALAY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kamus_alay.json')

def load_kamus_alay() -> Dict[str, str]:
    """Load kamus kata alay/gaul Bahasa Indonesia"""
    try:
        with open(KAMUS_ALAY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

KAMUS_ALAY = load_kamus_alay()

# Stopwords Indonesia
STOPWORDS_ID = set(stopwords.words('indonesian')) if 'indonesian' in stopwords.fileids() else set()

# Tambah stopword manual
CUSTOM_STOPWORDS = {
    'yg', 'dgn', 'dg', 'dlm', 'utk', 'pd', 'dr', 'jg', 'krn',
    'tp', 'trs', 'sdh', 'blm', 'jd', 'sm', 'km', 'sy', 'gw',
    'gue', 'lu', 'lo', 'deh', 'sih', 'lho', 'lah', 'dong', 'nih',
    'tu', 'itu', 'ini', 'nya', 'ku', 'mu', 'aja', 'aj', 'doang',
    'wkwk', 'wkwkwk', 'hehe', 'hihi', 'lol', 'omg', 'wtf',
    'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or',
    'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
}
STOPWORDS_ID = STOPWORDS_ID.union(CUSTOM_STOPWORDS)


# ─────────────────────────────────────────────────────────────────
# FUNGSI CLEANING INDIVIDUAL
# ─────────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """Deteksi bahasa teks menggunakan langdetect"""
    if not LANGDETECT_AVAILABLE or not text or len(text.strip()) < 5:
        return 'id'
    try:
        lang = detect(text)
        return lang
    except Exception:
        return 'id'


def lowercase(text: str) -> str:
    """Ubah teks menjadi huruf kecil"""
    return text.lower()


def remove_urls(text: str) -> str:
    """Hapus URL dari teks"""
    # HTTP/HTTPS URLs
    text = re.sub(r'https?://\S+', '', text)
    # www URLs
    text = re.sub(r'www\.\S+', '', text)
    # bit.ly, tinyurl, dll
    text = re.sub(r'\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co)/\S+', '', text)
    return text.strip()


def remove_mentions(text: str) -> str:
    """Hapus mention (@username) dari teks"""
    return re.sub(r'@\w+', '', text).strip()


def remove_hashtags(text: str) -> str:
    """Hapus hashtag (#topik) dari teks, pertahankan teksnya"""
    # Hapus simbol # tapi pertahankan kata setelahnya
    return re.sub(r'#(\w+)', r'\1', text).strip()


def remove_emojis(text: str) -> str:
    """Hapus emoji dari teks"""
    # Emoji ranges
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002500-\U00002BEF"  # chinese chars
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()


def remove_special_chars(text: str) -> str:
    """Hapus karakter khusus, pertahankan huruf dan angka"""
    # Hapus karakter non-alfanumerik kecuali spasi
    text = re.sub(r'[^\w\s]', ' ', text)
    # Hapus underscore
    text = re.sub(r'_', ' ', text)
    return text.strip()


def remove_numbers(text: str) -> str:
    """Hapus angka dari teks"""
    return re.sub(r'\d+', '', text).strip()


def remove_extra_whitespace(text: str) -> str:
    """Hapus spasi berlebih"""
    return re.sub(r'\s+', ' ', text).strip()


def normalize_alay(text: str) -> str:
    """Normalisasi kata-kata alay/gaul ke kata baku"""
    words = text.split()
    normalized = []
    for word in words:
        # Cek kata secara keseluruhan
        if word in KAMUS_ALAY:
            normalized.append(KAMUS_ALAY[word])
        else:
            normalized.append(word)
    return ' '.join(normalized)


def normalize_repeated_chars(text: str) -> str:
    """Normalisasi karakter berulang (misal: 'bagussss' → 'bagus')"""
    # Karakter yang berulang lebih dari 2x dikurangi jadi 2x
    return re.sub(r'(.)\1{2,}', r'\1\1', text)


def remove_stopwords(text: str) -> str:
    """Hapus stopword Bahasa Indonesia"""
    words = text.split()
    filtered = [w for w in words if w not in STOPWORDS_ID and len(w) > 1]
    return ' '.join(filtered)


def stem_text(text: str) -> str:
    """Stemming kata menggunakan Sastrawi"""
    if not SASTRAWI_AVAILABLE:
        return text
    return stemmer.stem(text)


def remove_html_tags(text: str) -> str:
    """Hapus HTML tags dari teks"""
    return re.sub(r'<[^>]+>', '', text)


def fix_encoding(text: str) -> str:
    """Perbaiki encoding karakter"""
    try:
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        # Encode ke ASCII dan decode kembali untuk menghapus karakter non-ASCII
        # text = text.encode('ascii', 'ignore').decode('ascii')
        return text
    except Exception:
        return text


# ─────────────────────────────────────────────────────────────────
# PIPELINE CLEANING UTAMA
# ─────────────────────────────────────────────────────────────────

class TextCleaner:
    """Pipeline pembersihan teks Bahasa Indonesia"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Inisialisasi TextCleaner dengan konfigurasi.
        
        Args:
            config: Dictionary berisi pengaturan cleaning.
                    Jika None, semua fitur diaktifkan.
        """
        self.config = config or {
            'detect_language': True,
            'lowercase': True,
            'remove_html': True,
            'fix_encoding': True,
            'remove_urls': True,
            'remove_mentions': True,
            'remove_hashtags': True,
            'remove_emojis': True,
            'normalize_alay': True,
            'normalize_repeated': True,
            'remove_special_chars': True,
            'remove_numbers': True,
            'remove_stopwords': True,
            'stemming': False,  # Off by default (mengubah makna)
            'remove_duplicates': True,
            'min_length': 3,
        }

    def clean_single(self, text: str, return_steps: bool = False) -> Dict:
        """
        Bersihkan satu teks dengan pipeline lengkap.
        
        Args:
            text: Teks yang akan dibersihkan
            return_steps: Jika True, kembalikan setiap langkah cleaning
            
        Returns:
            Dictionary berisi teks bersih dan metadata
        """
        if not text or not isinstance(text, str):
            return {
                'original': text,
                'cleaned': '',
                'language': 'unknown',
                'steps': {},
                'is_valid': False
            }

        result = {
            'original': text,
            'language': 'id',
            'steps': {},
            'is_valid': True
        }

        current = text

        # Step 1: Fix encoding
        if self.config.get('fix_encoding', True):
            current = fix_encoding(current)
            if return_steps:
                result['steps']['fix_encoding'] = current

        # Step 2: Deteksi bahasa
        if self.config.get('detect_language', True):
            result['language'] = detect_language(current)

        # Step 3: Hapus HTML
        if self.config.get('remove_html', True):
            current = remove_html_tags(current)
            if return_steps:
                result['steps']['remove_html'] = current

        # Step 4: Lowercase
        if self.config.get('lowercase', True):
            current = lowercase(current)
            if return_steps:
                result['steps']['lowercase'] = current

        # Step 5: Hapus URL
        if self.config.get('remove_urls', True):
            current = remove_urls(current)
            if return_steps:
                result['steps']['remove_urls'] = current

        # Step 6: Hapus mention
        if self.config.get('remove_mentions', True):
            current = remove_mentions(current)
            if return_steps:
                result['steps']['remove_mentions'] = current

        # Step 7: Hapus hashtag
        if self.config.get('remove_hashtags', True):
            current = remove_hashtags(current)
            if return_steps:
                result['steps']['remove_hashtags'] = current

        # Step 8: Hapus emoji
        if self.config.get('remove_emojis', True):
            current = remove_emojis(current)
            if return_steps:
                result['steps']['remove_emojis'] = current

        # Step 9: Normalisasi kata alay
        if self.config.get('normalize_alay', True):
            current = normalize_alay(current)
            if return_steps:
                result['steps']['normalize_alay'] = current

        # Step 10: Normalisasi karakter berulang
        if self.config.get('normalize_repeated', True):
            current = normalize_repeated_chars(current)
            if return_steps:
                result['steps']['normalize_repeated'] = current

        # Step 11: Hapus karakter khusus
        if self.config.get('remove_special_chars', True):
            current = remove_special_chars(current)
            if return_steps:
                result['steps']['remove_special_chars'] = current

        # Step 12: Hapus angka
        if self.config.get('remove_numbers', True):
            current = remove_numbers(current)
            if return_steps:
                result['steps']['remove_numbers'] = current

        # Step 13: Hapus whitespace berlebih
        current = remove_extra_whitespace(current)

        # Step 14: Hapus stopwords
        if self.config.get('remove_stopwords', True):
            current = remove_stopwords(current)
            if return_steps:
                result['steps']['remove_stopwords'] = current

        # Step 15: Stemming
        if self.config.get('stemming', False):
            current = stem_text(current)
            if return_steps:
                result['steps']['stemming'] = current

        # Final cleanup
        current = remove_extra_whitespace(current)

        # Validasi panjang minimum
        min_len = self.config.get('min_length', 3)
        if len(current.strip()) < min_len:
            result['is_valid'] = False

        result['cleaned'] = current
        result['word_count_before'] = len(text.split())
        result['word_count_after'] = len(current.split()) if current else 0
        result['char_count_before'] = len(text)
        result['char_count_after'] = len(current)

        return result

    def clean_batch(self, texts: List[str]) -> pd.DataFrame:
        """
        Bersihkan banyak teks sekaligus.
        
        Args:
            texts: List teks yang akan dibersihkan
            
        Returns:
            DataFrame berisi teks asli, teks bersih, dan metadata
        """
        results = []
        for text in texts:
            res = self.clean_single(text)
            results.append({
                'teks_asli': res['original'],
                'teks_bersih': res['cleaned'],
                'bahasa': res['language'],
                'jumlah_kata_asli': res.get('word_count_before', 0),
                'jumlah_kata_bersih': res.get('word_count_after', 0),
                'valid': res['is_valid']
            })

        df = pd.DataFrame(results)

        # Hapus duplikat jika dikonfigurasi
        if self.config.get('remove_duplicates', True):
            df = df.drop_duplicates(subset=['teks_bersih'])

        return df

    def get_cleaning_stats(self, df: pd.DataFrame) -> Dict:
        """Hitung statistik hasil cleaning"""
        total = len(df)
        valid = df['valid'].sum() if 'valid' in df.columns else total
        
        stats = {
            'total_teks': total,
            'teks_valid': int(valid),
            'teks_invalid': int(total - valid),
            'duplikat_dihapus': 0,
            'rata_kata_asli': round(df['jumlah_kata_asli'].mean(), 2) if 'jumlah_kata_asli' in df.columns else 0,
            'rata_kata_bersih': round(df['jumlah_kata_bersih'].mean(), 2) if 'jumlah_kata_bersih' in df.columns else 0,
        }
        
        if 'bahasa' in df.columns:
            stats['distribusi_bahasa'] = df['bahasa'].value_counts().to_dict()
        
        return stats
