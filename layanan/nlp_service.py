import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

import os

for res in ['punkt', 'stopwords']:
    try:
        nltk.data.find(f'corpora/{res}' if res == 'stopwords' else f'tokenizers/{res}')
    except LookupError:
        # Di Vercel, download ke /tmp agar bisa ditulis
        dl_dir = '/tmp/nltk_data' if os.environ.get('VERCEL') == '1' else None
        try:
            nltk.download(res, quiet=True, download_dir=dl_dir)
            if dl_dir:
                nltk.data.path.insert(0, dl_dir)
        except Exception:
            pass

try:
    _EN_STOPWORDS = set(stopwords.words('english'))
except LookupError:
    _EN_STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be',
        'this', 'that', 'it', 'its', 'my', 'your', 'our', 'their', 'i', 'you'
    }

STOPWORDS = _EN_STOPWORDS.union({
    'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk', 'pada',
    'dengan', 'adalah', 'saya', 'tidak', 'yg', 'nya', 'aja', 'saja',
    'akan', 'atau', 'juga', 'sudah', 'bisa', 'ada', 'karena', 'jadi'
})


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join([w for w in text.split() if w not in STOPWORDS and len(w) > 2])


POS_ID = {
    # Kualitas produk & layanan (UMKM/bisnis digital)
    'bagus', 'berkualitas', 'tinggi', 'mantap', 'keren', 'cepat', 'puas',
    'terbaik', 'hebat', 'membantu', 'suka', 'senang', 'nyaman', 'aman',
    'lancar', 'murah', 'promo', 'diskon', 'gratis', 'berhasil', 'terpercaya',
    'sukses', 'juara', 'rekomendasi', 'recommended', 'ramah', 'bersih', 'rapi',
    'sempurna', 'top', 'oke', 'sip', 'jos', 'mantul', 'unik',
    'menarik', 'asik', 'asyik', 'positif', 'unggul', 'memuaskan', 'worth',
    'good', 'great', 'best', 'awesome', 'amazing', 'happy', 'love', 'nice',
    # Ekonomi digital & bisnis
    'untung', 'profit', 'laris', 'laku', 'booming', 'viral', 'trending',
    'terjangkau', 'hemat', 'efisien', 'produktif', 'inovatif', 'kreatif',
    'tumbuh', 'berkembang', 'maju', 'omzet', 'pendapatan', 'investasi',
    'menguntungkan', 'potensial', 'peluang', 'ekspansi', 'digitalisasi',
    'mudah', 'praktis', 'cepet', 'responsif', 'profesional', 'amanah',
    'original', 'asli', 'genuine', 'resmi', 'legal', 'terjamin',
    # TikTok Shop / marketplace UMKM
    'estafet', 'ongkir', 'gratis_ongkir', 'cashback', 'voucher', 'flash_sale',
    'review_bagus', 'bintang', 'rating_tinggi', 'seller_terpercaya',
    'pengiriman_cepat', 'packaging_bagus', 'sesuai_ekspektasi', 'recommended',
    'repeat_order', 'langganan', 'loyal', 'worth_it', 'value', 'affordable'
}

NEG_ID = {
    # Keluhan produk & layanan
    'buruk', 'kecewa', 'parah', 'lambat', 'rugi', 'error', 'gagal', 'jelek',
    'sampah', 'benci', 'marah', 'kesal', 'mahal', 'lemot', 'macet',
    'rusak', 'cacat', 'palsu', 'penipu', 'bohong', 'hoax', 'susah', 'sulit',
    'ribet', 'bingung', 'bosan', 'mengecewakan', 'menyesal', 'hancur', 'kacau',
    'negatif', 'bahaya', 'toxic', 'scam', 'terburuk', 'payah',
    'terrible', 'bad', 'worst', 'hate', 'broken', 'fail', 'failed', 'slow', 'awful',
    # Keluhan khas ekonomi digital / UMKM / marketplace
    'tipu', 'ditipu', 'menipu', 'penipuan', 'modus', 'tidak_sampai', 'hilang',
    'retur', 'komplain', 'refund_gagal', 'uang_hilang', 'barang_palsu',
    'barang_tidak_sesuai', 'deskripsi_berbeda', 'beda_foto', 'seller_nakal',
    'respon_lama', 'tidak_responsif', 'admin_cuek', 'olshop_abal',
    'dropship_jelek', 'pengiriman_lama', 'ongkir_mahal', 'batal_sepihak',
    'diblokir', 'akun_dibekukan', 'stok_habis', 'tidak_jelas',
    'rugi_besar', 'bangkrut', 'gulung_tikar', 'merugi', 'defisit',
    'tidak_terpercaya', 'tidak_recommended', 'tidak_amanah', 'tidak_profesional'
}

NEGATIONS = {'tidak', 'bukan', 'tak', 'gak', 'ga', 'nggak', 'enggak', 'jangan', 'kurang', 'belum', 'not', 'no', 'never'}


def _analyze_textblob(text: str) -> dict:
    tokens = re.findall(r'\w+', text.lower())
    pos_score = 0
    neg_score = 0

    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else ''
        is_negated = prev in NEGATIONS
        if tok in POS_ID:
            if is_negated:
                neg_score += 1
            else:
                pos_score += 1
        elif tok in NEG_ID:
            if is_negated:
                pos_score += 1
            else:
                neg_score += 1

    if pos_score > neg_score:
        diff = pos_score - neg_score
        return {'sentiment': 'positive', 'confidence': min(98, 65 + diff * 12)}
    elif neg_score > pos_score:
        diff = neg_score - pos_score
        return {'sentiment': 'negative', 'confidence': min(98, 65 + diff * 12)}

    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return {'sentiment': 'positive', 'confidence': int(min(98, 58 + polarity * 40))}
    elif polarity < -0.1:
        return {'sentiment': 'negative', 'confidence': int(min(98, 58 + abs(polarity) * 40))}
    return {'sentiment': 'neutral', 'confidence': 52}


_TRAINING_DATA = [
    # ── POSITIVE: Ulasan produk & layanan UMKM / e-commerce ──────────────────
    ("produk ini sangat bagus dan berkualitas tinggi", "positive"),
    ("pelayanan sangat ramah cepat dan memuaskan", "positive"),
    ("barang sampai dengan aman packing rapi mantap", "positive"),
    ("sangat puas belanja disini recommended banget", "positive"),
    ("harga murah kualitas terbaik tidak mengecewakan", "positive"),
    ("aplikasi ini sangat membantu dan mudah digunakan", "positive"),
    ("pengiriman cepat respon admin baik sekali", "positive"),
    ("toko umkm lokal ini kualitasnya luar biasa mantul", "positive"),
    ("usaha kecil ini berkembang pesat omzetnya naik terus", "positive"),
    ("promo cashback voucher diskon sangat menguntungkan pembeli", "positive"),
    ("produk lokal indonesia bagus banget worth it terpercaya", "positive"),
    ("seller responsif amanah profesional repeat order terus", "positive"),
    ("digitalisasi umkm ini membantu sekali pendapatan naik", "positive"),
    ("bisnis online ini tumbuh pesat inovatif dan kreatif", "positive"),
    ("tiktok shop umkm lokal ini laris viral trending", "positive"),
    ("great product works fast and affordable love it", "positive"),
    # ── NEGATIVE: Keluhan produk / marketplace / bisnis digital ──────────────
    ("pelayanan sangat buruk sangat kecewa parah", "negative"),
    ("barang rusak cacat tidak sesuai deskripsi rugi", "negative"),
    ("penipu hoax palsu jangan beli dari toko ini", "negative"),
    ("pengiriman lama ongkir mahal seller tidak responsif", "negative"),
    ("uang sudah transfer barang tidak sampai ditipu", "negative"),
    ("produk palsu tidak asli beda dari foto deskripsi berbeda", "negative"),
    ("komplain tidak ditanggapi refund gagal admin cuek", "negative"),
    ("olshop abal-abal modus penipuan jangan percaya", "negative"),
    ("bisnis ini bangkrut merugi tidak professional sama sekali", "negative"),
    ("aplikasi error lambat susah dipakai bikin rugi", "negative"),
    ("harga mahal kualitas sampah menyesal beli ini", "negative"),
    ("umkm ini tidak berkembang karena pelayanan buruk kacau", "negative"),
    ("stok habis batal sepihak tidak amanah mengecewakan", "negative"),
    ("terrible experience broken product and slow delivery", "negative"),
    ("scam seller worst experience hate this shop", "negative"),
    ("respon lama admin tidak ramah sangat buruk", "negative"),
    # ── NEUTRAL: Informasi / deskripsi / laporan ekonomi digital ─────────────
    ("info harga paket internet terbaru untuk usaha", "neutral"),
    ("cara mendaftar toko umkm di marketplace online", "neutral"),
    ("panduan digitalisasi umkm langkah demi langkah", "neutral"),
    ("laporan pertumbuhan ekonomi digital indonesia tahun ini", "neutral"),
    ("perbandingan platform e-commerce untuk jualan online", "neutral"),
    ("cara menginstall aplikasi kasir untuk warung", "neutral"),
    ("daftar program bantuan pemerintah untuk umkm", "neutral"),
    ("statistik pengguna tiktok shop dan shopee indonesia", "neutral"),
    ("review spesifikasi laptop untuk kebutuhan kerja bisnis", "neutral"),
    ("pengumuman update fitur baru aplikasi pembayaran digital", "neutral"),
    ("panduan cara membuka rekening bisnis online", "neutral"),
    ("perbandingan ongkos kirim jne jnt sicepat", "neutral"),
    ("cara buat konten promosi produk umkm di media sosial", "neutral"),
    ("ringkasan berita ekonomi digital minggu ini", "neutral"),
    ("tutorial membuat website toko online gratis", "neutral"),
    ("info program kur kredit usaha rakyat 2026", "neutral"),
]

_SAMPLES = [t for t, _ in _TRAINING_DATA]
_LABELS = [l for _, l in _TRAINING_DATA]
_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
_clf = MultinomialNB(alpha=0.5).fit(_vec.fit_transform(_SAMPLES), _LABELS)


def _analyze_sklearn(text: str) -> dict:
    X = _vec.transform([text.lower()])
    if X.nnz == 0:
        # Fallback ke lexicon jika tidak ada kata yang cocok di vocabulary
        return _analyze_textblob(text)
    pred = _clf.predict(X)[0]
    prob = int(round(max(_clf.predict_proba(X)[0]) * 100))
    return {'sentiment': pred, 'confidence': prob}


_bert_pipe = None


def _analyze_bert(text: str) -> dict:
    global _bert_pipe
    try:
        if _bert_pipe is None:
            from transformers import pipeline
            _bert_pipe = pipeline(
                "sentiment-analysis",
                model="mdhugol/indonesia-bert-sentiment-classification"
            )
        out = _bert_pipe(text[:512])[0]
        lbl = out['label'].upper()
        conf = int(round(out['score'] * 100))
        if 'POS' in lbl or lbl == 'LABEL_0':
            return {'sentiment': 'positive', 'confidence': conf}
        elif 'NEG' in lbl or lbl == 'LABEL_2':
            return {'sentiment': 'negative', 'confidence': conf}
        return {'sentiment': 'neutral', 'confidence': conf}
    except ImportError:
        return _analyze_sklearn(text)


def analyze_sentiment(text: str, engine: str = 'textblob') -> dict:
    if engine == 'sklearn':
        return _analyze_sklearn(text)
    elif engine == 'bert':
        return _analyze_bert(text)
    return _analyze_textblob(text)


def extract_top_keywords(texts: list, top_n: int = 10) -> list:
    words = []
    for t in texts:
        words.extend(clean_text(t).split())
    return Counter(words).most_common(top_n)
